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

from tcms.apps.management.models import Product
from tcms.apps.management.models import TestBuild
from tcms.apps.testcases.models import TestCase
from tcms.apps.testplans.models import TestPlan
from tcms.apps.testruns.models import TestCaseRun
from tcms.apps.testruns.models import TestRun
from tcms.core.utils.xmlrpc import XMLRPCSerializer


class TestSerializationBackwardCompatibility(unittest.TestCase):
    '''Ensure new serialization method to generate same data with original

    Remove this test when migrate to new serialization completely.
    '''

    def _test_backward_compatible(self, model_class, object_pk):
        '''Ensure new serialization method to generate same data'''

        base_object = model_class.objects.get(pk=object_pk)
        sample_result = model_class.to_xmlrpc(query={'pk': object_pk})[0]
        base_result = XMLRPCSerializer(model=base_object).serialize_model()

        sample_fields = [name for name in sample_result.keys()]
        base_fields = [name for name in base_result.keys()]

        # Ensure fields are same.
        test_result = list(set(sample_fields) - set(base_fields))
        self.assertEqual(test_result, [])
        test_result = list(set(base_fields) - set(sample_fields))
        self.assertEqual(test_result, [])

        # Ensure values are same.
        for sample_field, sample_value in sample_result.iteritems():
            self.assertEqual(sample_value, base_result[sample_field])

    def test_testplan(self):
        self._test_backward_compatible(TestPlan, 12563)

    def test_testcase(self):
        self._test_backward_compatible(TestCase, 341602)

    def test_testrun(self):
        self._test_backward_compatible(TestRun, 43718)

    def test_testcaserun(self):
        self._test_backward_compatible(TestCaseRun, 3479449)

    def test_testbuild(self):
        self._test_backward_compatible(TestBuild, 573)

    def test_product(self):
        self._test_backward_compatible(Product, 301)


if __name__ == '__main__':
    unittest.main()