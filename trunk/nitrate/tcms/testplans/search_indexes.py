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

# from tcms
from tcms.testplans.models import TestPlan

class PlanIndexer(indexes.SearchIndex):
    summary         = indexes.CharField(model_attr='name', document=True, null=True)
    author          = indexes.CharField(model_attr='author__username', null=True)
    plan_id         = indexes.IntegerField(model_attr='pk', null=True)
    plan_type       = indexes.IntegerField(model_attr='type_id', null=True)
    is_active       = indexes.BooleanField(model_attr='is_active', null=True)
    create_date     = indexes.DateTimeField(model_attr='create_date', null=True)
    product         = indexes.IntegerField(null=True)
    version         = indexes.IntegerField(null=True)
    component       = indexes.MultiValueField(null=True)
    tags            = indexes.MultiValueField(null=True)
    # Related models. In haystack, when building indexes on a o2m or m2m field,
    # you need to supply a function to prepare the data.
    # http://groups.google.com/group/django-haystack/browse_thread/thread/ec47cbde86d5231d/c139f5e063f4b4d9?#c139f5e063f4b4d9

    case_ids        = indexes.MultiValueField(indexed=False, null=True)
    run_ids         = indexes.MultiValueField(indexed=False, null=True)

    def prepare_product(self, obj):
        return [obj.product_id]

    def prepare_component(self, obj):
        return [c.pk for c in obj.component.all()]

    def prepare_version(self, obj):
        return obj.get_version_id()

    def prepare_tags(self, obj):
        return [
            t.name for t in obj.tag.all()
        ]

    def prepare_case_ids(self, obj):
        return [c.pk for c in obj.case.all()]

    def prepare_run_ids(self, obj):
        return [r.pk for r in obj.run.all()]

site.register(TestPlan, PlanIndexer)
