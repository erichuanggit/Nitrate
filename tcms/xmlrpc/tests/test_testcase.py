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

from tcms.apps.testcases.models import TestCase


class TestTestCaseSerialization(unittest.TestCase):

    test_fields = (
        'case_id',
        'create_date',
        'is_automated',
        'is_automated_proposed',
        'script',
        'arguments',
        'extra_link',
        'summary',
        'requirement',
        'alias',
        'estimated_time',
        'notes',

        'case_status', 'case_status_id',
        'category', 'category_id',
        'priority', 'priority_id',
        'author', 'author_id',
        'default_tester', 'default_tester_id',
        'reviewer', 'reviewer_id',

        'attachment', 'plan', 'component', 'tag',
    )

    def setUp(self):
        self.case_pks = (341602, 341603)

    def test_to_xmlrpc(self):
        result = TestCase.to_xmlrpc(query={'pk__in': self.case_pks})
        self.assertEqual(len(result), 2)

        # Verify fields
        sample_testcase = result[0]
        sample_fields = set([name for name in sample_testcase.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        result = dict([(item['case_id'], item) for item in result])

        case = result[self.case_pks[0]]
        sample_case = TestCase.objects.get(pk=self.case_pks[0])

        self.assertEqual(case['is_automated'], sample_case.is_automated)
        self.assertEqual(case['summary'], sample_case.summary)
        self.assertEqual(case['alias'], sample_case.alias)

        self.assertEqual(case['author'], sample_case.author.username)
        self.assertEqual(case['author_id'], sample_case.author.pk)
        self.assertEqual(case['priority'], sample_case.priority.value)
        self.assertEqual(case['priority_id'], sample_case.priority.pk)

        components = case['component']
        components.sort()
        sample_components = [item.pk for item in sample_case.component.all()]
        sample_components.sort()
        self.assertEqual(components, sample_components)

        tags = case['tag']
        tags.sort()
        sample_tags = [item.pk for item in sample_case.tag.all()]
        sample_tags.sort()
        self.assertEqual(tags, sample_tags)


if __name__ == '__main__':
    unittest.main()
