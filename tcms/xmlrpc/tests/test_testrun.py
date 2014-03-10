# -*- coding: utf-8 -*-

import unittest

from tcms.apps.testruns.models import TestRun


class TestTestRun(unittest.TestCase):

    def setUp(self):
        self.testrun_pks = (43718, 43717)

    def test_to_xmlrpc(self):
        testrun1 = TestRun.objects.get(pk=self.testrun_pks[0])
        testrun2 = TestRun.objects.get(pk=self.testrun_pks[1])

        result = TestRun.to_xmlrpc(query={'pk__in': self.testrun_pks})
        self.assertEqual(len(result), 2)

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