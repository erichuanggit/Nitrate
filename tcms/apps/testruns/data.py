# -*- coding: utf-8 -*-
#
# Nitrate is copyright 2010-2014 Red Hat, Inc.
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
#   Chenxiong Qi <cqi@redhat.com>

from itertools import izip
from itertools import groupby

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection

from tcms.apps.testcases.models import TestCaseBug
from tcms.apps.testruns.models import TestCaseRun
from tcms.apps.testruns.models import TestCaseRunStatus


def stats_caseruns_status(case_runs, case_run_statuss):
    '''Get statistics based on case runs' status

    @return: the statistics including the number of each status mapping,
        complete percent, and failure percent.
    @rtype: tuple
    '''
    caserun_statuss_subtotal = dict([(status.name, [0, status])
                                    for status in case_run_statuss])
    complete_count = 0
    failure_count = 0
    status_complete_names = TestCaseRunStatus.complete_status_names
    status_failure_names = TestCaseRunStatus.failure_status_names

    for case_run in case_runs:
        status_name = case_run.case_run_status.name
        caserun_statuss_subtotal[status_name][0] += 1
        if status_name in status_complete_names:
            complete_count += 1
        if status_name in status_failure_names:
            failure_count += 1

    # Final calculation
    complete_percent = complete_count * 100.0 / len(case_runs)
    failure_percent = .0
    if complete_count:
        failure_percent = failure_count * 100.0 / complete_count

    return caserun_statuss_subtotal, complete_percent, failure_percent


def get_caseruns_bug_ids(run_id):
    '''Get case runs' bug ids

    @param run_id: from whose case runs to get bug ids
    @type: int
    @return: bug ids
    @rtype: iterable object
    '''
    bug_ids = TestCaseBug.objects.filter(
        case_run__run_id=run_id).values_list('bug_id', flat=True)
    return set(bug_ids.iterator())


class TestCaseRunDataMixin(object):
    '''Data for test case runs'''

    def stats_mode_caseruns(self, case_runs):
        '''Statistics from case runs mode

        @param case_runs: iteratable object to access each case run
        @type case_runs: iterable, list, tuple
        @return: mapping between mode and the count. Example return value is
            { 'manual': I, 'automated': J, 'manual_automated': N }
        @rtype: dict
        '''
        manual_count = 0
        automated_count = 0
        manual_automated_count = 0

        for case_run in case_runs:
            is_automated = case_run.case.is_automated
            if is_automated == 1:
                automated_count += 1
            elif is_automated == 0:
                manual_count += 1
            else:
                manual_automated_count += 1

        return {'manual': manual_count,
                'automated': automated_count,
                'manual_automated': manual_automated_count,
                }

    def get_caseruns_bugs(self, run_pk):
        '''Get case run bugs for run report

        @param run_pk: run's pk whose case runs' bugs will be retrieved.
        @type run_pk: int
        @return: the mapping between case run id and bugs
        @rtype: dict
        '''
        cursor = connection.cursor()

        sql = '''
            SELECT test_case_runs.case_run_id,
                test_case_bugs.bug_id,
                test_case_bug_systems.url_reg_exp
            FROM test_case_runs
            INNER JOIN test_case_bugs
                ON (test_case_runs.case_run_id = test_case_bugs.case_run_id)
            INNER JOIN test_case_bug_systems
                ON (test_case_bugs.bug_system_id = test_case_bug_systems.id)
            WHERE test_case_runs.run_id = %s
            ORDER BY test_case_runs.case_run_id'''
        cursor.execute(sql, [run_pk,])
        field_names = [field[0] for field in cursor.description]
        rows = []
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            row = dict(izip(field_names, row))
            row['bug_url'] = row['url_reg_exp'] % row['bug_id']
            rows.append(row)
        return dict(groupby(rows, lambda row: row['case_run_id']))

    def get_caseruns_comments(self, run_pk):
        '''Get case runs' comments

        @param run_pk: run's pk whose comments will be retrieved.
        @type run_pk: int
        @return: the mapping between case run id and comments
        @rtype: dict
        '''
        sql = '''
            select test_case_runs.case_run_id, auth_user.username,
                django_comments.submit_date, django_comments.comment
            from test_case_runs
            inner join django_comments
                on (test_case_runs.case_run_id = django_comments.object_pk)
            inner join auth_user on (django_comments.user_id = auth_user.id)
            where django_comments.site_id = %s and
                django_comments.content_type_id = %s and
                django_comments.is_public = 1 and
                django_comments.is_removed = 0 and
                test_case_runs.run_id = %s
            ORDER BY test_case_runs.case_run_id'''
        ct = ContentType.objects.get_for_model(TestCaseRun)
        cursor = connection.cursor()
        cursor.execute(sql, [settings.SITE_ID, ct.pk, run_pk,])
        field_names = [field[0] for field in cursor.description]
        rows = []
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            rows.append(dict(izip(field_names, row)))
        return dict(groupby(rows, lambda row: row['case_run_id']))

    def get_summary_stats(self, case_runs):
        '''Get summary statistics from case runs

        Statistics targets:
        - the number of pending test case runs, whose status is IDLE
        - the number of completed test case runs, whose status are PASSED,
          ERROR, FAILED, WAIVED

        @param case_runs: iterable object containing case runs
        @type case_runs: iterable
        @return: a mapping between statistics target and its value
        @rtype: dict
        '''
        idle_count = 0
        complete_count = 0
        complete_status_names = TestCaseRunStatus.complete_status_names
        idle_status_names = TestCaseRunStatus.idle_status_names

        for case_run in case_runs:
            status_name = case_run.case_run_status.name
            if status_name in idle_status_names:
                idle_count += 1
            elif status_name in complete_status_names:
                complete_count += 1

        return {'idle': idle_count, 'complete': complete_count}
