# -*- coding: utf-8 -*-

import unittest

from tcms.apps.testplans.models import TestPlan


class TestTestPlan(unittest.TestCase):

    def setUp(self):
        self.plan_pks = (12563, 5240)

    def test_to_xmlrpc(self):
        result = TestPlan.to_xmlrpc(query={'pk__in': self.plan_pks})
        self.assertEqual(len(result), 2)

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
