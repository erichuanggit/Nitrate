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
