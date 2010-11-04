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
from django.db.models import signals

from tcms.core.models import TCMSActionModel, TimedeltaField
from tcms.testcases.models import TestCaseBug, TestCaseText, NoneText

from signals import post_run_saved

# Create your models here.

class TestRun(TCMSActionModel):
    # plan_id = models.IntegerField()
    # environment_id = models.IntegerField()
    # build_id = models.IntegerField()
    # manager_id = models.IntegerField()
    # default_tester_id = models.IntegerField(null=True, blank=True)
    
    run_id = models.AutoField(primary_key=True)
    
    product_version = models.CharField(max_length=192, blank=True)
    plan_text_version = models.IntegerField()
    
    start_date = models.DateTimeField(auto_now_add=True)
    stop_date = models.DateTimeField(null=True, blank=True)
    summary = models.TextField()
    notes = models.TextField(blank=True)
    estimated_time = TimedeltaField()
    
    plan = models.ForeignKey('testplans.TestPlan', related_name='run')
    environment_id = models.IntegerField(default=0)
    build = models.ForeignKey('management.TestBuild', related_name='build_run')
    manager = models.ForeignKey(
        'auth.User', related_name='manager'
    )
    default_tester = models.ForeignKey(
        'auth.User', related_name='default_tester', null = True,
    )
    #case = models.ManyToManyField(
    #    'testcases.TestCase',
    #    through='testcases.TestCaseRun',
    #    related_name='run_case'
    #)
    
    env_value = models.ManyToManyField(
        'management.TCMSEnvValue',
        through='testruns.TCMSEnvRunValueMap',
    )
    
    tag = models.ManyToManyField(
        'management.TestTag',
        through='testruns.TestRunTag',
    )
    
    cc = models.ManyToManyField(
        'auth.User',
        through='testruns.TestRunCC',
    )
    
    # Auto-generated attributes from back-references:
    #   'caseruns' : query on TestCaseRuns (from TestCaseRuns.run)
    
    class Meta:
        db_table = u'test_runs'
        unique_together = ('run_id', 'product_version', 'plan_text_version')
        ordering = ['-run_id', 'summary']
    
    def __unicode__(self):
        return self.summary
    
    @classmethod
    def list(cls, query):
        from django.db.models import Q
        
        q = cls.objects
        
        if query.get('search'):
           q = q.filter(
                Q(run_id__icontains = query['search']) |
                Q(summary__icontains = query['search'])
            )
        
        if query.get('summary'):
            q = q.filter(summary__icontains = query['summary'])
        
        if query.get('product'):
            q = q.filter(build__product = query['product'])
        
        if query.get('product_version'):
            q = q.filter(product_version = query['product_version'])
        
        plan_str = query.get('plan')
        if plan_str:
            try:
                # Is it an integer?  If so treat as a plan_id:
                plan_id = int(plan_str)
                q = q.filter(plan__plan_id = plan_id)
            except ValueError:
                # Not an integer - treat plan_str as a plan name:
                q = q.filter(plan__name__icontains = plan_str)
        del plan_str
        
        if query.get('build'):
            q = q.filter(build = query['build'])
        
        # Old style environment search
        #if query.get('env_id'):
        #    q = q.filter(environment__environment_id = query.get('env_id'))
        
        # New environment search
        if query.get('env_group'):
            q = q.filter(plan__env_group = query['env_group'])
        
        if query.get('people_id'):
            q = q.filter(
                Q(manager__id = query['people_id'])
                | Q(default_tester__id = query['people_id'])
            )
        
        if query.get('people'):
            q = q.filter(
                Q(manager__first_name__startswith = query['people'])
                | Q(manager__last_name__startswith = query['people'])
                | Q(manager__username__icontains = query['people'])
                | Q(manager__email__startswith = query['people'])
                | Q(default_tester__first_name__startswith = query['people'])
                | Q(default_tester__last_name__startswith = query['people'])
                | Q(default_tester__username__icontains = query['people'])
                | Q(default_tester__email__startswith = query['people'])
        )
        elif query.get('manager'):
            q = q.filter(
                Q(manager__first_name__startswith = query['manager'])
                | Q(manager__last_name__startswith = query['manager'])
                | Q(manager__username__icontains = query['manager'])
                | Q(manager__email__startswith = query['manager'])
        )
        elif query.get('default_tester'):
            q = q.filter(
                Q(default_tester__first_name__startswith = query['default_tester'])
                | Q(default_tester__last_name__startswith = query['default_tester'])
                | Q(default_tester__username__icontains = query['default_tester'])
                | Q(default_tester__email__startswith = query['default_tester'])
            )
        
        if query.get('sortby'):
            q = q.order_by(query.get('sortby'))
        
        if query.get('status'):
            if query.get('status').lower() == 'running':
                q = q.filter(stop_date__isnull = True)
            if query.get('status').lower() == 'finished':
                q = q.filter(stop_date__isnull = False)
        
        if query.get('tag__name__in'):
            q = q.filter(tag__name__in = query['tag__name__in'])
        
        if query.get('case_run__assignee__email__startswith'):
            q = q.filter(case_run__assignee__email__startswith = query['case_run__assignee__email__startswith'])
        
        return q.distinct()
    
    def belong_to(self, user):
        if self.manager == user or self.plan.author == user:
            return True
            
        return False
    
    def check_all_case_runs(self, case_run_id = None):
        tcrs = self.case_run.all()
        tcrs = tcrs.select_related('case_run_status')
        
        if case_run_id:
            for tcr in tcrs:
                if tcr.is_current:
                    tcr.is_current = False
                    tcr.save()
                    
                if tcr.case_run_id == case_run_id:
                    try:
                        prev_tcr, next_tcr = tcr.get_previous_or_next()
                        next_tcr.is_current = True
                        next_tcr.save()
                    except:
                        raise
        
        for tcr in tcrs:
            if not tcr.is_finished():
                return False
        
        return True
    
    def get_absolute_url(self, request = None):
        # Upward compatibility code
        if request:
            return request.build_absolute_uri(
                reverse('tcms.testruns.views.get', args=[self.pk, ])
            )
        
        return self.get_url(request)
    
    def get_notify_addrs(self):
        """
        Get the all related mails from the run
        """
        to = [self.manager.email]
        to.extend(self.cc.values_list('email', flat=True))
        if self.default_tester_id:
            to.append(self.default_tester.email)
            
        for tcr in self.case_run.select_related('assignee').all():
            if tcr.assignee_id:
                to.append(tcr.assignee.email)
        return list(set(to))
    
    def get_url_path(self):
        return reverse('tcms.testruns.views.get', args=[self.pk, ])
    
    def get_product_version(self):
        """
        Workaround the schema problem with default_product_version
        Get a 'Versions' object based on a string query
        """
        from tcms.management.models import Version
        try:
            return Version.objects.get(
                product = self.build.product,
                value = self.product_version
            )
        except Version.DoesNotExist:
            return None
    
    def get_version_id(self):
        """
        Workaround the schema problem with default_product_version
        """
        version = self.get_product_version()
        return version and version.id or None
    
    def add_case_run(self, case, case_run_status = 1, assignee = None, case_text_version = None, build = None, notes = None, sortkey = 0):
        try:
            return self.case_run.create(
                case = case,
                assignee = assignee or (
                    case.default_tester_id and case.default_tester
                ) or (
                    self.default_tester_id and self.default_tester
                ),
                tested_by = None,
                case_run_status = isinstance(case_run_status, int) \
                    and TestCaseRunStatus.objects.get(id = case_run_status) \
                    or case_run_status,
                case_text_version = case_text_version or case.latest_text().case_text_version,
                build = build or self.build,
                notes = notes,
                sortkey = sortkey,
                environment_id = self.environment_id,
                running_date = None,
                close_date = None,
                is_current = False,
            )
        except:
            raise
    
    def add_tag(self, tag):
        try:
            return TestRunTag.objects.get_or_create(
                run = self,
                tag = tag
            )
        except:
            raise
    
    def add_cc(self, user):
        try:
            return TestRunCC.objects.get_or_create(
                run = self,
                user = user,
            )
        except:
            raise
    
    def add_env_value(self, env_value):
        try:
            return TCMSEnvRunValueMap.objects.get_or_create(
                run = self,
                value = env_value,
            )
        except:
            raise
    
    def remove_tag(self, tag):
        cursor = connection.cursor()
        cursor.execute("DELETE from test_run_tags \
            WHERE run_id = %s \
            AND tag_id = %s", 
            (self.pk, tag.pk)
        )
    
    def remove_cc(self, user):
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE from test_run_cc \
                WHERE run_id = %s \
                AND who = %s", 
                (self.run_id, user.id)
            )
        except:
            raise
    
    def remove_env_value(self, env_value):
        try:
            run_env_value = TCMSEnvRunValueMap.objects.get(
                run = self,
                value = env_value,
            )
            run_env_value.delete()
        except:
            raise
    
    def mail(self, template, subject, context, to = [], request = None):
        from tcms.core.utils.mailto import mailto
        to = self.get_notify_addrs()
        mailto(template, subject, to, context, request)

class TestCaseRunStatus(TCMSActionModel):
    id = models.AutoField(db_column='case_run_status_id', primary_key=True)
    name = models.CharField(max_length=60, blank=True)
    sortkey = models.IntegerField(null=True, blank=True, default=0)
    description = models.TextField(null=True, blank=True)
    auto_blinddown = models.BooleanField(default=1)
    
    class Meta:
        db_table = u'test_case_run_status'
        ordering = ['sortkey', 'name', 'id']
    
    def __unicode__(self):
        return unicode(self.name)
    
    def is_finished(self):
        if self.name in ['PASSED', 'FAILED', 'ERROR', 'WAIVED']:
            return True
        
        return False
    
    @classmethod
    def get_IDLE(cls):
        try:
            return cls.objects.get(name = 'IDLE')
        except:
            raise
    
    @classmethod
    def id_to_string(cls, id):
        try:
            return cls.objects.get(id = id).name
        except cls.DoesNotExist:
            return None

class TestCaseRun(TCMSActionModel):
    case_run_id = models.AutoField(primary_key=True)
    assignee = models.ForeignKey(
        'auth.User',
        blank=True,
        null=True,
        related_name='case_run_assignee'
    )
    tested_by = models.ForeignKey(
        'auth.User',
        blank = True,
        null=True,
        related_name='case_run_tester'
    )
    case_text_version = models.IntegerField()
    running_date = models.DateTimeField(null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_current = models.BooleanField(db_column="iscurrent")
    sortkey = models.IntegerField(null=True, blank=True)
    
    run = models.ForeignKey(TestRun, related_name='case_run')
    case = models.ForeignKey('testcases.TestCase', related_name='case_run')
    case_run_status = models.ForeignKey(TestCaseRunStatus)
    build = models.ForeignKey('management.TestBuild')
    environment_id = models.IntegerField(default=0)
    
    class Meta:
        db_table = u'test_case_runs'
        unique_together = ('case', 'run', 'case_text_version')
        ordering = ['sortkey', 'case_run_id']
    
    def __unicode__(self):
        return '%s: %s' % (self.pk, self.case_id)
    
    @classmethod
    def mail_scene(cls, objects, field = None, value = None, ctype = None, object_pk = None):
        tr = objects[0].run
        # scence_templates format:
        # template, subject, context
        tcrs = objects.select_related()
        scence_templates = {
            'assignee': {
                'template_name': 'mail/change_case_run_assignee.txt',
                'subject': 'Assignee of run %s has been changed' % tr.run_id,
                'to_mail': tr.get_notify_addrs(),
                'context': {'test_run': tr, 'test_case_runs': tcrs},
            }
        }
        
        return scence_templates.get(field)
    
    def add_bug(self, bug_id, bug_system, summary = None, description = None):
        try:
            return self.case.add_bug(
                bug_id = bug_id,
                bug_system = bug_system,
                summary = summary,
                description = description,
                case_run = self,
            )
        except:
            raise
    
    def remove_bug(self, id):
        try:
            bug = self.case_run_bug.get(id = id)
            bug.delete()
        except:
            raise
    
    def is_finished(self):
        return self.case_run_status.is_finished()
    
    def get_bugs(self):
        return TestCaseBug.objects.filter(case_run__case_run_id = self.case_run_id)
    
    def get_text_versions(self):
        return TestCaseText.objects.filter(
            case__pk = self.case.pk
        ).values_list('case_text_version', flat=True)
    
    def get_text_with_version(self, case_text_version = None):
        if case_text_version:
            try:
                return TestCaseText.objects.get(
                    case__case_id = self.case_id,
                    case_text_version = case_text_version
                )
            except TestCaseText.DoesNotExist, error:
                return NoneText
        try:
            return TestCaseText.objects.get(
                case__case_id = self.case_id,
                case_text_version = self.case_text_version
            )
        except TestCaseText.DoesNotExist:
            return NoneText
    
    def get_previous_or_next(self):
        ids = list(self.run.case_run.values_list('case_run_id', flat=True))
        current_idx = ids.index(self.case_run_id)
        prev = TestCaseRun.objects.get(case_run_id = ids[current_idx - 1])
        try:
            next = TestCaseRun.objects.get(case_run_id = ids[current_idx + 1])
        except IndexError:
            next = TestCaseRun.objects.get(case_run_id = ids[0])
            
        return (prev, next)
    
    def latest_text(self):
        try:
            return TestCaseText.objects.filter(
                case__case_id = self.case_id
            ).order_by('-case_text_version')[0]
        except IndexError:
            return NoneText
    
    def set_current(self):
        for case_run in self.run.case_run.all():
            if case_run.is_current:
                case_run.is_current = False
                case_run.save()
                
        self.is_current = True
        self.save()

class TestRunTag(models.Model):
    tag = models.ForeignKey(
        'management.TestTag', primary_key=True
    )
    run = models.ForeignKey(TestRun)
    user = models.IntegerField(db_column='userid', default='0')
    
    class Meta:
        db_table = u'test_run_tags'

class TestRunCC(models.Model):
    run = models.ForeignKey(TestRun, primary_key=True)
    user = models.ForeignKey('auth.User', db_column='who')
    
    class Meta:
        db_table = u'test_run_cc'

class TCMSEnvRunValueMap(models.Model):
    run = models.ForeignKey(TestRun)
    value = models.ForeignKey('management.TCMSEnvValue')
    
    class Meta:
        db_table = u'tcms_env_run_value_map'

# Signals handler
signals.post_save.connect(post_run_saved, sender=TestRun)
