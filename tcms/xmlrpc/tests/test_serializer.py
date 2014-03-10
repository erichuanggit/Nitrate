# -*- coding: utf-8 -*-

import unittest

from pprint import pprint

from tcms.apps.testcases.models import TestCase
from tcms.core.utils.xmlrpc import XMLRPCSerializer


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.testcase_pk = 315663
        self.testcase = TestCase.objects.get(pk=self.testcase_pk)

    def test_serializer(self):
        serializer = XMLRPCSerializer(model=self.testcase)

        result = serializer.serialize_model()

        self.assertEqual(self.testcase.category.pk, result['category_id'])
        self.assertEqual(str(self.testcase.category), result['category'])

        component_pks = [c.pk for c in self.testcase.component.all()]
        component_pks.sort()
        result['component'].sort()
        self.assertEqual(component_pks, result['component'])

        self.assertEqual(self.testcase.alias, result['alias'])
        self.assertEqual(self.testcase.arguments, result['arguments'])

if __name__ == '__main__':
    unittest.main()
