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

from tcms.apps.testruns.models import TestRun


class TestTestRun(unittest.TestCase):

    test_fields = (
        'run_id',
        'errata_id',
        'product_version',
        'plan_text_version',
        'start_date',
        'stop_date',
        'summary',
        'notes',
        'estimated_time',
        'environment_id',
        'auto_update_run_status',

        'plan', 'plan_id',
        'build', 'build_id',
        'manager', 'manager_id',
        'default_tester', 'default_tester_id',

        'env_value', 'tag', 'cc',
    )

    def setUp(self):
        self.testrun_pks = (43718, 43717)

    def test_to_xmlrpc(self):
        testrun1 = TestRun.objects.get(pk=self.testrun_pks[0])
        testrun2 = TestRun.objects.get(pk=self.testrun_pks[1])

        result = TestRun.to_xmlrpc(query={'pk__in': self.testrun_pks})
        self.assertEqual(len(result), 2)

        # Verify fields
        sample_testrun = result[0]
        sample_fields = set([name for name in sample_testrun.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        result = dict([(item['run_id'], item) for item in result])

        sample_testrun1 = result[self.testrun_pks[0]]
        sample_testrun2 = result[self.testrun_pks[1]]

        self.assertEqual(testrun1.errata_id, sample_testrun1['errata_id'])
        self.assertEqual(testrun1.product_version, sample_testrun1['product_version'])
        self.assertEqual(testrun1.default_tester.pk, sample_testrun1['default_tester_id'])
        self.assertEqual(testrun1.default_tester.username, sample_testrun1['default_tester'])

        tags = [tag.pk for tag in testrun1.tag.all()]
        tags.sort()
        sample_tags = sample_testrun1['tag']
        sample_tags.sort()
        self.assertEqual(tags, sample_tags)


if __name__ == '__main__':
    unittest.main()
