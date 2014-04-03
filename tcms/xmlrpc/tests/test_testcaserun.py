# -*- coding: utf-8 -*-
#
# Nitrate is copyright 2014 Red Hat, Inc.
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


import unittest

from django.contrib.auth.models import User

from tcms.xmlrpc.testcaserun import update


class FakeRequest(object):

    def __init__(self):
        self.user = User.objects.get(username='cqi')


class TestCaseForRunUpdate(unittest.TestCase):
    '''Specific to testcaserun.update method

    Test for fixing issue TCMS-122

    Sample TestCaseRuns: 3479449, 3479450, 3479451
    '''

    test_fields = (
        'case_run_id',
        'case_text_version',
        'running_date',
        'close_date',
        'notes',
        'is_current',
        'sortkey',
        'environment_id',

        'assignee', 'assignee_id',
        'tested_by', 'tested_by_id',
        'run', 'run_id',
        'case', 'case_id',
        'case_run_status', 'case_run_status_id',
        'build', 'build_id',

        'links',
    )

    def setUp(self):
        self.user = User.objects.get(username='cqi')
        self.request = FakeRequest()

    def test_update(self):
        tcrs_to_update = [3479449, 3479450, 3479451]
        data_to_update = {
            'notes': 'test testcaserun.update',
            'assignee': self.user.pk,
        }

        updated_tcrs = update(self.request, tcrs_to_update, data_to_update)

        self.assertEqual(len(updated_tcrs), 3)

        # Verify all fields are serialized correctly
        sample_tcr = updated_tcrs[0]
        sample_fields = set([name for name in sample_tcr.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        test_pks = [item['case_run_id'] for item in updated_tcrs]
        test_pks.sort()
        self.assertEqual(tcrs_to_update, test_pks)

        test_notes = [item['notes'] for item in updated_tcrs]
        for notes in test_notes:
            self.assertEqual(data_to_update['notes'], str(notes))

        test_assignees = [(item['assignee'], item['assignee_id'])
                          for item in updated_tcrs]
        for assignee, assignee_id in test_assignees:
            self.assertEqual(assignee, self.user.username)
            self.assertEqual(assignee_id, self.user.pk)


if __name__ == '__main__':
    unittest.main()
