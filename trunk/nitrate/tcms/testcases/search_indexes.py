# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
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
#   Xuqing Kuang <xkuang@redhat.com>, Chaobin Tang <ctang@redhat.com>

# from django

# from stdlib
from haystack import indexes, site
from datetime import datetime

# from tcms
from tcms.testcases.models import TestCase

class TestCaseIndexer(indexes.SearchIndex):
    case_id         = indexes.IntegerField(model_attr='pk')
    summary         = indexes.CharField(model_attr='summary', document=True, null=True)
    author          = indexes.CharField(model_attr='author__username', null=True)
    tester          = indexes.CharField(null=True)
    status          = indexes.IntegerField(model_attr='case_status_id', null=True)
    is_automated    = indexes.BooleanField(model_attr='is_automated', null=True)
    is_auto_prop    = indexes.BooleanField(model_attr='is_automated_proposed', null=True)
    priority        = indexes.IntegerField(model_attr='priority_id', null=True)
    script          = indexes.CharField(model_attr='script', null=True)
    create_date     = indexes.DateTimeField(model_attr='create_date', null=True)
    category        = indexes.IntegerField(model_attr='category__id', null=True)

    plan_ids        = indexes.MultiValueField(null=True, indexed=False)
    run_ids         = indexes.MultiValueField(null=True, indexed=False)
    tags            = indexes.MultiValueField(null=True)
    bugs            = indexes.MultiValueField(null=True)
    components      = indexes.MultiValueField(null=True)
    product         = indexes.MultiValueField(null=True)

    def prepare_product(self, obj):
        products = [o['product_id']
            for o in obj.component.values('product_id')
        ]
        products.append(obj.category.product_id)
        return products

    def prepare_components(self, obj):
        return [
            c.pk for c in obj.component.all()
        ]

    def prepare_tags(self, obj):
        return [
            t.name for t in obj.tag.all()
        ]

    def prepare_bugs(self, obj):
        return [
            b.pk for b in obj.case_bug.all()
        ]

    def prepare_tester(self, obj):
        try:
            tester =  obj.default_tester.username
        except:
            tester = None
        return tester

    def prepare_plan_ids(self, obj):
        return [p.pk for p in obj.plan.all()]

    def prepare_run_ids(self, obj):
        runs = obj.case_run.values('run')
        return [r['run'] for r in runs]

site.register(TestCase, TestCaseIndexer)
