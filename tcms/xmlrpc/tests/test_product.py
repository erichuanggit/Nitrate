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


class TestProduct(unittest.TestCase):

    test_fields = (
        'id',
        'name',
        'description',
        'milestone_url',
        'disallow_new',
        'vote_super_user',
        'max_vote_super_bug',
        'votes_to_confirm',
        'default_milestone',

        'classification', 'classification_id',
    )

    def setUp(self):
        self.product = Product.objects.get(pk=301)

    def test_to_xmlrpc(self):
        result = Product.to_xmlrpc(query={'pk': self.product.pk})
        self.assertEqual(len(result), 1)

        # Verify fields
        sample_product = result[0]
        sample_fields = set([name for name in sample_product.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        sample_product = result[0]
        self.assertEqual(self.product.name, sample_product['name'])
        self.assertEqual(self.product.description, sample_product['description'])
        self.assertEqual(self.product.classification.pk,
                         sample_product['classification_id'])
        self.assertEqual(self.product.classification.name,
                         sample_product['classification'])


if __name__ == '__main__':
    unittest.main()
