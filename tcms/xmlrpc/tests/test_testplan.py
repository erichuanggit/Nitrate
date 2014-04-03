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

from tcms.apps.testplans.models import TestPlan


class TestTestPlan(unittest.TestCase):

    test_fields = (
        'plan_id',
        'default_product_version',
        'name',
        'create_date',
        'is_active',
        'extra_link',

        # foreign keys
        'product_version', 'product_version_id',
        'owner', 'owner_id',
        'author', 'author_id',
        'product', 'product_id',
        'type', 'type_id',
        'parent', 'parent_id',

        # m2m fields
        'attachment',
        'case',
        'component',
        'env_group',
        'tag',
    )

    def setUp(self):
        self.plan_pks = (12563, 5240)

    def test_to_xmlrpc(self):
        result = TestPlan.to_xmlrpc(query={'pk__in': self.plan_pks})
        self.assertEqual(len(result), 2)

        # Verify fields
        sample_testplan = result[0]
        sample_fields = set([name for name in sample_testplan.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        result = dict([(item['plan_id'], item) for item in result])

        plan = result[self.plan_pks[0]]
        sample_plan = TestPlan.objects.get(pk=self.plan_pks[0])

        self.assertEqual(plan['default_product_version'],
                         sample_plan.default_product_version)
        self.assertEqual(plan['name'], sample_plan.name)
        self.assertEqual(plan['is_active'], sample_plan.is_active)

        components = plan['component']
        components.sort()
        sample_components = [item.pk for item in sample_plan.component.all()]
        sample_components.sort()
        self.assertEqual(components, sample_components)

        plan = result[self.plan_pks[1]]
        sample_plan = TestPlan.objects.get(pk=self.plan_pks[1])

        self.assertEqual(plan['default_product_version'],
                         sample_plan.default_product_version)
        self.assertEqual(plan['name'], sample_plan.name)
        self.assertEqual(plan['is_active'], sample_plan.is_active)


if __name__ == '__main__':
    unittest.main()
