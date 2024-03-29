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

import datetime

from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes import generic
from django.conf import settings

from tcms.apps.testcases.models import TestCaseBug, TestCaseText, NoneText
from tcms.apps.testruns import signals as run_watchers
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.models import TCMSActionModel, TimedeltaField

try:
    from tcms.core.contrib.plugins_support.signals import register_model
except ImportError:
    register_model = None


class TestRun(TCMSActionModel):

    # Attribute names to get testrun statistics
    PERCENTAGES = (
        'failed_case_run_percent',
        'passed_case_run_percent', 
        'completed_case_run_percent')

    run_id = models.AutoField(primary_key=True)
    errata_id = models.IntegerField(max_length=11, null=True, blank=True)

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
    manager = models.ForeignKey('auth.User', related_name='manager')
    default_tester = models.ForeignKey('auth.User',
                                       null=True, blank=True,
                                       related_name='default_tester')

    env_value = models.ManyToManyField('management.TCMSEnvValue',
                                       through='testruns.TCMSEnvRunValueMap')

    tag = models.ManyToManyField('management.TestTag',
                                 through='testruns.TestRunTag')

    cc = models.ManyToManyField('auth.User', through='testruns.TestRunCC')
    auto_update_run_status = models.BooleanField(default=False)

    class Meta:
        db_table = u'test_runs'
        unique_together = ('run_id', 'product_version', 'plan_text_version')

    def __unicode__(self):
        return self.summary

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.core.utils.xmlrpc import TestRunXMLRPCSerializer
        from tcms.xmlrpc.utils import distinct_filter

        _query = query or {}
        qs = distinct_filter(TestRun, _query).order_by('pk')
        s = TestRunXMLRPCSerializer(model_class=cls, queryset=qs)
        return s.serialize_queryset()

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

        # New environment search
        if query.get('env_group'):
            q = q.filter(plan__env_group = query['env_group'])

        if query.get('people_id'):
            q = q.filter(
                Q(manager__id = query['people_id'])
                | Q(default_tester__id = query['people_id'])
            )

        if query.get('people'):
            if query.get('people_type') == 'default_tester':
                q = q.filter(default_tester = query['people'])
            elif query.get('people_type') == 'manager':
                q = q.filter(manager = query['people'])
            else:
                q = q.filter(
                    Q(manager = query['people'])
                    | Q(default_tester = query['people'])
                )

        if query.get('manager'):
            q = q.filter(manager = query['manager'])

        if query.get('default_tester'):
            q = q.filter(default_tester = query['default_tester'])

        if query.get('sortby'):
            q = q.order_by(query.get('sortby'))

        if query.get('status'):
            if query.get('status').lower() == 'running':
                q = q.filter(stop_date__isnull = True)
            if query.get('status').lower() == 'finished':
                q = q.filter(stop_date__isnull = False)

        if query.get('tag__name__in'):
            q = q.filter(tag__name__in = query['tag__name__in'])

        if query.get('case_run__assignee'):
            q = q.filter(case_run__assignee = query['case_run__assignee'])

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
                    prev_tcr, next_tcr = tcr.get_previous_or_next()
                    next_tcr.is_current = True
                    next_tcr.save()

        for tcr in tcrs:
            if not tcr.is_finished():
                return False

        return True

    def get_absolute_url(self, request = None):
        # Upward compatibility code
        if request:
            return request.build_absolute_uri(
                reverse('tcms.apps.testruns.views.get', args=[self.pk, ])
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
        return reverse('tcms.apps.testruns.views.get', args=[self.pk, ])

    def get_product_version(self):
        """
        Workaround the schema problem with default_product_version
        Get a 'Versions' object based on a string query
        """
        from tcms.apps.management.models import Version
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

    # FIXME: rewrite to use multiple values INSERT statement
    def add_case_run(self, case, case_run_status=1, assignee=None, case_text_version=None, build=None, notes=None, sortkey=0):
        _case_text_version = case_text_version
        if not _case_text_version:
            _case_text_version = case.latest_text(
                text_required=False).case_text_version

        _assignee = assignee or \
                    (case.default_tester_id and case.default_tester) or \
                    (self.default_tester_id and self.default_tester)

        get_caserun_status = TestCaseRunStatus.objects.get
        _case_run_status = isinstance(case_run_status, int) and \
                           get_caserun_status(id=case_run_status) or \
                           case_run_status

        return self.case_run.create(case=case,
                                    assignee=_assignee,
                                    tested_by=None,
                                    case_run_status=_case_run_status,
                                    case_text_version=_case_text_version,
                                    build=build or self.build,
                                    notes=notes,
                                    sortkey=sortkey,
                                    environment_id=self.environment_id,
                                    running_date=None,
                                    close_date=None,
                                    is_current=False)

    def add_tag(self, tag):
        return TestRunTag.objects.get_or_create(
            run = self,
            tag = tag
        )

    def add_cc(self, user):
        return TestRunCC.objects.get_or_create(
            run = self,
            user = user,
        )

    def add_env_value(self, env_value):
        return TCMSEnvRunValueMap.objects.get_or_create(
            run = self,
            value = env_value,
        )

    def remove_tag(self, tag):
        cursor = connection.cursor()
        cursor.execute("DELETE from test_run_tags \
            WHERE run_id = %s \
            AND tag_id = %s",
            (self.pk, tag.pk)
        )

    def remove_cc(self, user):
        cursor = connection.cursor()
        cursor.execute("DELETE from test_run_cc \
            WHERE run_id = %s \
            AND who = %s",
            (self.run_id, user.id)
        )

    def remove_env_value(self, env_value):
        run_env_value = TCMSEnvRunValueMap.objects.get(
            run = self,
            value = env_value,
        )
        run_env_value.delete()

    def mail(self, template, subject, context, to = [], request = None):
        from tcms.core.utils.mailto import mailto
        to = self.get_notify_addrs()
        mailto(template, subject, to, context, request)

    def get_bug_count(self):
        tcrs = self.case_run.all()
        tcr_bugs = TestCaseBug.objects.filter(case_run__case_run_id__in=tcrs.values_list('case_run_id', flat=True)).values('bug_id').distinct()
        return tcr_bugs.count()

    def get_percentage(self, count):
        case_run_count = self.total_num_caseruns
        if case_run_count == 0:
            return 0
        percent = float(count)/case_run_count*100
        percent = round(percent, 2)
        return percent

    def _get_completed_case_run_percentage(self):
        ids = TestCaseRunStatus._get_completed_status_ids()
        completed_caserun = self.case_run.filter(
            case_run_status__in=ids)
        
        percentage =  self.get_percentage(completed_caserun.count())
        return percentage
    completed_case_run_percent = property(_get_completed_case_run_percentage)

    def _get_failed_case_run_num(self):
        failed_status_id = TestCaseRunStatus.id_failed()
        failed_caserun = self.case_run.filter(
            case_run_status=failed_status_id
        )
        return failed_caserun.count()
    failed_case_run_num = property(_get_failed_case_run_num)

    def _get_failed_case_run_percentage(self):
        percentage = self.get_percentage(self.failed_case_run_num)
        return percentage
    failed_case_run_percent = property(_get_failed_case_run_percentage)

    def _get_passed_case_run_num(self):
        passed_status_id = TestCaseRunStatus.id_passed()
        passed_caserun = self.case_run.filter(
            case_run_status=passed_status_id
        )
        return passed_caserun.count()
    passed_case_run_num = property(_get_passed_case_run_num)

    def _get_passed_case_run_percentage(self):
        percentage = self.get_percentage(self.passed_case_run_num)
        return percentage
    passed_case_run_percent = property(_get_passed_case_run_percentage)

    def get_status_case_run_num(self, status_name):
        status_id = TestCaseRunStatus._status_to_id(status_name)
        caserun = self.case_run.filter(
            case_run_status=status_id
        )
        return caserun.count()

    def _get_total_case_run_num(self):
        return self.case_run.count()
    total_num_caseruns = property(_get_total_case_run_num)

    def update_completion_status(self, is_auto_updated, is_finish=None):
        if is_auto_updated and self.auto_update_run_status:
            if self.completed_case_run_percent == 100.0:
                self.stop_date = datetime.datetime.now()
            else:
                self.stop_date = None
            self.save()
        if not is_auto_updated and not self.auto_update_run_status:
            if is_finish:
                self.stop_date = datetime.datetime.now()
            else:
                self.stop_date = None
            self.save()


class TestCaseRunStatus(TCMSActionModel):

    complete_status_names = ('PASSED', 'ERROR', 'FAILED', 'WAIVED')
    failure_status_names = ('ERROR', 'FAILED')
    idle_status_names = ('IDLE',)

    id = models.AutoField(db_column='case_run_status_id', primary_key=True)
    name = models.CharField(max_length=60, blank=True, unique=True)
    sortkey = models.IntegerField(null=True, blank=True, default=0)
    description = models.TextField(null=True, blank=True)
    auto_blinddown = models.BooleanField(default=1)

    class Meta:
        db_table = u'test_case_run_status'

    def __unicode__(self):
        return unicode(self.name)

    def is_finished(self):
        if self.name in ['PASSED', 'FAILED', 'ERROR', 'WAIVED']:
            return True
        return False

    @classmethod
    def get_IDLE(cls):
        key = 'IDLE'
        result = cls.cache_get(key)
        if result is None:
            result = cls.cache_set(key, cls.objects.get(name = 'IDLE'))
        return result

    @classmethod
    def id_to_string(cls, _id):
        key = 'id_to_string_' + str(_id)
        result = cls.cache_get(key)
        if result is None:
            try:
                result = cls.objects.get(id=_id).name
            except cls.DoesNotExist:
                result = None
            cls.cache_set(key, result)
        return result

    @classmethod
    def _status_to_id(cls, status):
        status = status.upper()
        key = 'status_to_id_' + status
        result = cls.cache_get(key)
        if result is None:
            try:
                result = cls.objects.get(name=status).pk
            except cls.DoesNotExist:
                result = None
            cls.cache_set(key, result)
        return result

    @classmethod
    def _get_completed_status_ids(cls):
        '''
        There are some status indicate that
        the testcaserun is completed.
        Return IDs of these statuses.
        '''
        key = 'completed_status_ids'
        result = cls.cache_get(key)
        if result is None:
            completed_status = cls.objects.filter(name__in=(
                'FAILED', 'PASSED', 'ERROR', 'WAIVED'
            ))

            result = completed_status.values_list('pk', flat=True)
            result = cls.cache_set(key, list(result))
        return result

    @classmethod
    def _get_failed_status_ids(cls):
        '''
        There are some status indicate that
        the testcaserun is failed.
        Return IDs of these statuses.
        '''
        key = 'failed_status_ids'
        result = cls.cache_get(key)
        if result is None:
            statuses = cls.objects.all()
            failed_status = statuses.filter(name__in=(
                'FAILED', 'ERROR'
            ))

            result = failed_status.values_list('pk', flat=True)
            result = cls.cache_set(key, list(result))
        return result

    @classmethod
    def id_passed(cls):
        key = 'id_passed'
        result = cls.cache_get(key)
        if result is None:
            return cls.cache_set(key, cls._status_to_id('passed'))
        return result

    @classmethod
    def id_failed(cls):
        key = 'id_failed'
        result = cls.cache_get(key)
        if result is None:
            return cls.cache_set(key, cls._status_to_id('failed'))
        return result

    @classmethod
    def _get_cache(cls):
        """A dictionary used to cache statuses.

        The caching implementation in here is a
        dedicated cache for this class. There are
        limited few number of statuses, and they
        are needed frequently enough to be cached.
        """
        key_cache = '_cache'
        cache = getattr(cls, key_cache, {})
        if not hasattr(cls, key_cache):
            setattr(cls, key_cache, cache)

        return cache

    @classmethod
    def cache_get(cls, key):
        cache = cls._get_cache()
        return cache.get(key, None)

    @classmethod
    def cache_set(cls, key, value):
        cache = cls._get_cache()
        if len(cache) > 1000: # Prevent overflow
            cache.clear()
        cache[key] = value
        return value

    def save(self, *args, **kwargs):
        """Overrides save() only to outdate the cached statuses."""
        cache = getattr(self.__class__, '_cache', {})
        cache.clear()

        super(self.__class__, self).save(*args, **kwargs)


class TestCaseRunManager(models.Manager):

    def get_automated_case_count(self):
        return self.filter(case__is_automated = 1).count()

    def get_manual_case_count(self):
        return self.filter(case__is_automated = 0).count()

    def get_both(self):
        count1 = self.get_automated_case_count()
        count2 = self.get_manual_case_count()
        return self.count() - count1 - count2

    def get_caserun_failed_count(self):
        return self.filter(case_run_status__name = 'failed').count()

    def get_caserun_passed_count(self):
        return self.filter(case_run_status__name = 'passed').count()


class TestCaseRun(TCMSActionModel):
    objects = TestCaseRunManager()
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

    links = generic.GenericRelation(LinkReference, object_id_field='object_pk')

    class Meta:
        db_table = u'test_case_runs'
        unique_together = ('case', 'run', 'case_text_version')

    def __unicode__(self):
        return '%s: %s' % (self.pk, self.case_id)

    @classmethod
    def to_xmlrpc(cls, query={}):
        from tcms.core.utils.xmlrpc import TestCaseRunXMLRPCSerializer
        from tcms.xmlrpc.utils import distinct_filter

        qs = distinct_filter(TestCaseRun, query).order_by('pk')
        s = TestCaseRunXMLRPCSerializer(model_class=cls, queryset=qs)
        return s.serialize_queryset()

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
        return self.case.add_bug(
            bug_id = bug_id,
            bug_system = bug_system,
            summary = summary,
            description = description,
            case_run = self,
        )

    def remove_bug(self, bug_id, run_id=None):
        self.case.remove_bug(bug_id = bug_id, run_id=run_id)

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
        'management.TestTag'
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
def _run_listen():
    post_save.connect(run_watchers.post_run_saved, sender=TestRun)
    post_save.connect(run_watchers.post_case_run_saved, sender=TestCaseRun, dispatch_uid='tcms.apps.testruns.models.TestCaseRun')
    post_delete.connect(run_watchers.post_case_run_deleted, sender=TestCaseRun, dispatch_uid='tcms.apps.testruns.models.TestCaseRun')

if settings.LISTENING_MODEL_SIGNAL:
    _run_listen()

if register_model:
    register_model(TestRun)
    register_model(TestCaseRun)
    register_model(TestRunTag)
