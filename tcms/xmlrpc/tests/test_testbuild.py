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

from tcms.apps.management.models import TestBuild


class TestTestBuildSerialization(unittest.TestCase):

    test_fields = (
        'build_id',
        'name',
        'milestone',
        'description',
        'is_active',

        'product', 'product_id',
    )

    def setUp(self):
        self.test_build = TestBuild.objects.get(pk=573)

    def test_to_xmlrpc(self):
        result = TestBuild.to_xmlrpc(query={'pk': self.test_build.pk})
        self.assertEqual(len(result), 1)

        # Verify all fields are serialized correctly
        sample_testbuild = result[0]
        sample_fields = set([name for name in sample_testbuild.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        sample_tb = result[0]
        self.assertEqual(self.test_build.name, sample_tb['name'])
        self.assertEqual(self.test_build.product.pk, sample_tb['product_id'])
        self.assertEqual(self.test_build.product.name, sample_tb['product'])
        self.assertEqual(self.test_build.milestone, sample_tb['milestone'])
        self.assertEqual(self.test_build.is_active, sample_tb['is_active'])


if __name__ == '__main__':
    unittest.main()
