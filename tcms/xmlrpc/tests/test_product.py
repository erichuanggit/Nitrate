# -*- coding: utf-8 -*-

import unittest

from tcms.apps.management.models import Product


class TestProduct(unittest.TestCase):

    def setUp(self):
        self.product = Product.objects.get(pk=301)

    def test_to_xmlrpc(self):
        result = Product.to_xmlrpc(query={'pk': self.product.pk})
        self.assertEqual(len(result), 1)

        sample_product = result[0]
        self.assertEqual(self.product.name, sample_product['name'])
        self.assertEqual(self.product.description, sample_product['description'])
        self.assertEqual(self.product.classification.pk,
                         sample_product['classification_id'])
        self.assertEqual(self.product.classification.name,
                         sample_product['classification'])


if __name__ == '__main__':
    unittest.main()