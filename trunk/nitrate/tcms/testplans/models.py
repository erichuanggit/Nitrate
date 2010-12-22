# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
# 
# Authors:
#   Xuqing Kuang <xkuang@redhat.com>

from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models, connection, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.utils.safestring import mark_safe, SafeData

from tcms.management.models import TCMSEnvPlanMap
from tcms.testcases.models import TestCasePlan
from tcms.core.models import TCMSActionModel

try:
    from tcms.core.contrib.plugins_support.signals import register_model
except ImportError:
    register_model = None

class TestPlanType(TCMSActionModel):
    id = models.AutoField(db_column='type_id', primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)
    def __unicode__(self):
        return self.name
        
    class Meta:
        db_table = u'test_plan_types'
        ordering = ['name']

class TestPlan(TCMSActionModel):
    """
    A plan within the TCMS
    """
    plan_id = models.AutoField(max_length=11, primary_key=True)
    # product_id = models.IntegerField(max_length=6)
    # author_id = models.IntegerField(max_length=9)
    # type_id = models.IntegerField(max_length=4)
    
    # Unfortunately, default_product_version is a text field,
    # rather than a foreign key into the "versions" table:
    default_product_version = models.TextField()    
    name = models.CharField(max_length=255)
    create_date = models.DateTimeField(db_column='creation_date', auto_now_add=True)
    is_active = models.BooleanField(db_column='isactive', default=True)
    extra_link = models.CharField(
        max_length=1024,
        default=None,
        blank=True,
        null=True
    )
    
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child_set')
    author = models.ForeignKey('auth.User')
    product = models.ForeignKey('management.Product', related_name='plan')
    type = models.ForeignKey(TestPlanType)
    
    attachment = models.ManyToManyField(
        'management.TestAttachment',
        through='testplans.TestPlanAttachment',
    )
    
    case = models.ManyToManyField(
        'testcases.TestCase',
        through='testcases.TestCasePlan',
    )
    
    component = models.ManyToManyField(
        'management.Component', through='testplans.TestPlanComponent',
    )
    
    env_group = models.ManyToManyField(
        'management.TCMSEnvGroup',
        through='management.TCMSEnvPlanMap',
    )
    
    tag = models.ManyToManyField(
        'management.TestTag',
        through='testplans.TestPlanTag',
    )
    
    # Auto-generated attributes from back-references:
    #   'cases' : list of TestCases (from TestCases.plans)
    
    class Meta:
        db_table = u'test_plans'
        ordering = ['-plan_id', 'name']
    
    def __unicode__(self):
        return self.name
    
    def confirmed_case(self):
        return self.case.filter(case_status__name = 'CONFIRMED')
    
    def latest_text(self):
        try:
            return self.text.select_related('author').order_by('-plan_text_version')[0]
        except IndexError:
            return None
        except ObjectDoesNotExist:
            return None
    
    def get_text_with_version(self, plan_text_version = None):
        if plan_text_version:
            try:
                return self.text.get(
                    plan_text_version = plan_text_version
                )
            except TestPlanText.DoesNotExist, error:
                return None
        
        return self.latest_text()
    
    def add_text(self,
        author,
        plan_text,
        create_date = datetime.now(),
        plan_text_version = None
    ):
        if not plan_text_version:
            latest_text = self.latest_text()
            if latest_text:
                plan_text_version = latest_text.plan_text_version + 1
            else:
                plan_text_version = 1
        
        try:
            return self.text.create(
                plan_text_version = plan_text_version,
                author = author,
                create_date = create_date,
                plan_text = plan_text
            )
        except:
            raise
    
    def add_case(self, case):
        try:
            return TestCasePlan.objects.create(
                plan = self,
                case = case,
            )
        except:
            return False
    
    def add_component(self, component):
        try:
            return TestPlanComponent.objects.create(
                plan = self,
                component = component,
            )
        except:
            return False
    
    def add_env_group(self, env_group):
        # Create the env plan map
        try:
            return TCMSEnvPlanMap.objects.create(
                plan = self,
                group = env_group,
            )
        except:
            raise
    
    def add_attachment(self, attachment):
        try:
            return TestPlanAttachment.objects.create(
                plan = self,
                attachment = attachment,
            )
        except:
            raise
    
    def add_tag(self, tag):
        try:
            return TestPlanTag.objects.get_or_create(
                plan = self,
                tag = tag
            )
        except:
            raise
    
    def remove_tag(self, tag):
        cursor = connection.cursor()
        cursor.execute("DELETE from test_plan_tags \
            WHERE plan_id = %s \
            AND tag_id = %s", 
            (self.pk, tag.pk)
        )
    
    def remove_component(self, component):
        try:
            return TestPlanComponent.objects.get(
                plan = self, component = component
            ).delete()
        except:
            return False
    
    def clear_env_groups(self):
        # Remove old env groups because we only maintanence on group per plan.
        try:
            return TCMSEnvPlanMap.objects.filter(plan = self).delete()
        except:
            raise
    
    def delete_case(self, case):
        cursor = connection.cursor()
        cursor.execute("DELETE from test_case_plans \
            WHERE plan_id = %s \
            AND case_id = %s", 
            (self.plan_id, case.case_id)
        )
    
    def get_absolute_url(self, request = None):
        # Upward compatibility code
        if request:
            return request.build_absolute_uri(
                reverse('tcms.testplans.views.get', args=[self.pk, ])
            )
        
        return self.get_url(request)
    
    def get_url_path(self, request = None):
        return reverse('tcms.testplans.views.get', args=[self.pk, ])
    
    def get_default_product_version(self):
        """
        Workaround the schema problem with default_product_version
        Get a 'Versions' object based on a string query
        """
        from tcms.management.models import Version
        try:
            return Version.objects.get(
                product = self.product,
                value = self.default_product_version
            )
        except ObjectDoesNotExist:
            return None
    
    def get_version_id(self):
        """
        Workaround the schema problem with default_product_version
        """
        version = self.get_default_product_version()
        return version and version.id or None

setattr(TestPlan._meta, 'exclude_fields', ['action'])

class TestPlanText(TCMSActionModel):
    plan = models.ForeignKey(
        TestPlan,
        related_name='text',
        db_index=True,
        primary_key=True
    )
    plan_text_version = models.IntegerField(max_length=11, db_index=True)
    author = models.ForeignKey('auth.User', db_column='who')
    create_date = models.DateTimeField(auto_now_add=True, db_column='creation_ts')
    plan_text = models.TextField(blank=True)
    class Meta:
        db_table = u'test_plan_texts'
        ordering = ['plan', '-plan_text_version']
        unique_together = ('plan', 'plan_text_version')
    def get_plain_text(self):
        from tcms.core.utils.html import html2text
        
        self.plan_text = html2text(self.plan_text)
        
        return self

class TestPlanPermission(models.Model):
    userid = models.IntegerField(max_length=9, unique=True, primary_key=True)
    permissions = models.IntegerField(max_length=4)
    grant_type = models.IntegerField(max_length=4, unique=True)
    
    plan = models.ForeignKey(TestPlan)
    
    class Meta:
        db_table = u'test_plan_permissions'
        unique_together = ('plan', 'userid')
    
class TestPlanPermissionsRegexp(models.Model):
    plan = models.ForeignKey(TestPlan, primary_key=True)
    user_regexp = models.TextField()
    permissions = models.IntegerField(max_length=4)
    class Meta:
        db_table = u'test_plan_permissions_regexp'

class TestPlanAttachment(models.Model):
    attachment = models.ForeignKey(
        'management.TestAttachment',
        primary_key=True
    )
    plan = models.ForeignKey(TestPlan)
    class Meta:
        db_table = u'test_plan_attachments'

class TestPlanActivity(models.Model):
    plan = models.ForeignKey(TestPlan) # plan_id
    fieldid = models.IntegerField()
    who = models.ForeignKey('auth.User', db_column='who')
    changed = models.DateTimeField(primary_key=True)
    oldvalue = models.TextField(blank=True)
    newvalue = models.TextField(blank=True)
    class Meta:
        db_table = u'test_plan_activity'

class TestPlanTag(models.Model):
    tag = models.ForeignKey(
        'management.TestTag', primary_key=True
    )
    plan = models.ForeignKey(TestPlan)
    user = models.IntegerField(default="1", db_column='userid')
    
    class Meta:
        db_table = u'test_plan_tags'

class TestPlanComponent(models.Model):
    plan = models.ForeignKey(TestPlan)
    component = models.ForeignKey('management.Component')
    
    class Meta:
        db_table = u'test_plan_components'
        unique_together = ('plan', 'component')

if register_model:
    register_model(TestPlan)
    register_model(TestPlanText)
    register_model(TestPlanType)
    register_model(TestPlanTag)
    register_model(TestPlanComponent)
