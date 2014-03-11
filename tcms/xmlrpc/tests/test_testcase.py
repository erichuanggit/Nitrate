# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import unittest

from tcms.apps.testcases.models import TestCase


class TestTestCase(unittest.TestCase):

    def setUp(self):
        self.case_pks = (341602, 341603)

    def test_to_xmlrpc(self):
        result = TestCase.to_xmlrpc(query={'pk__in': self.case_pks})
        self.assertEqual(len(result), 2)

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
