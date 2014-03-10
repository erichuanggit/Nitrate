# -*- coding: utf-8 -*-

import unittest

from tcms.apps.management.models import TestBuild


class TestTestBuild(unittest.TestCase):

    def setUp(self):
        self.test_build = TestBuild.objects.get(pk=573)

    def test_to_xmlrpc(self):
        result = TestBuild.to_xmlrpc(query={'pk': self.test_build.pk})
        self.assertEqual(len(result), 1)

        sample_tb = result[0]
        self.assertEqual(self.test_build.name, sample_tb['name'])
        self.assertEqual(self.test_build.product.pk, sample_tb['product_id'])
        self.assertEqual(self.test_build.product.name, sample_tb['product'])
        self.assertEqual(self.test_build.milestone, sample_tb['milestone'])
        self.assertEqual(self.test_build.is_active, sample_tb['is_active'])


if __name__ == '__main__':
    unittest.main()