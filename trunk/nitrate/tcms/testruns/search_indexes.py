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
from tcms.testruns.models import TestRun

class TestRunIndexer(indexes.SearchIndex):
    run_id      = indexes.IntegerField(model_attr='pk')
    summary     = indexes.CharField(model_attr='summary', document=True, null=True)
    manager     = indexes.CharField(model_attr='manager__username', null=True)
    tester      = indexes.CharField(model_attr='default_tester__username', null=True)
    is_finished = indexes.BooleanField(null=True)
    plan        = indexes.IntegerField(model_attr='plan__pk', null=True)
    build       = indexes.IntegerField(model_attr='build_id', null=True)
    product     = indexes.IntegerField(model_attr='build__product_id', null=True)

    # NOTE: is_finished attr on testrun is determined on existence of stop_date
    finished    = indexes.BooleanField(null=True)
    start_date  = indexes.DateTimeField(model_attr='start_date', null=True)
    stop_date   = indexes.DateTimeField(model_attr='stop_date', null=True)
    tags        = indexes.MultiValueField(null=True)
    real_tester = indexes.MultiValueField(null=True)

    case_ids    = indexes.CharField(null=True)


    def prepare_real_tester(self, obj):
        key   = 'tested_by__username'
        names = obj.case_run.values(key)
        return ' '.join([
            str(n[key]) for n in names if n
        ])

    def prepare_tags(self, obj):
        return [
            t.name for t in obj.tag.all()
        ]

    def prepare_case_ids(self, obj):
        cases   = obj.case_run.values('case')
        return ' '.join([
            str(c['case']) for c in cases
        ])

    def prepare_is_finished(self, obj):
        return bool(obj.stop_date)

site.register(TestRun, TestRunIndexer)
