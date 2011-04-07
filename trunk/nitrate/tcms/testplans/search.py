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

'''
Advance search implementations
'''

# from django
from django.http import HttpResponse, Http404
from django import template
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.conf import settings
from django.db.models import Q
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.management.color import termcolors

# from tcms
from tcms.testplans.models import TestPlan, TestPlanType
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestRun
from tcms.management.models import Product, Version, Priority

# from stdlib
from datetime import datetime
from functools import partial
from itertools import chain
from tcms.haystack.query import SearchQuerySet
import time

# while debugging, using the following shortcuts
# to colorize the command line output.
G           = partial(termcolors.colorize, fg='green') # Green -> healthy
R           = partial(termcolors.colorize, fg='red') # Red -> warning

# a template creating a charfield with required = False
LooseCF     = partial(forms.CharField, required=False)
LooseIF     = partial(forms.IntegerField, required=False)
LooseDF     = partial(forms.DateField, required=False)

def cached_entities(ctype_name):
    '''
    Some entities are frequently used.\n
    Cache them for reuse.\n
    Retrieve using model names.
    '''
    ctype_key   = 'ctt_type_' + ctype_name
    c_type      = cache.get(ctype_key)
    if not c_type:
        c_type  = ContentType.objects.get(model__iexact=ctype_name)
        cache.set(ctype_key, c_type)
    model_class = c_type.model_class()
    key         = 'cached_' + ctype_name
    entities    = cache.get(key)
    if not entities:
        entities    = model_class._default_manager.all()
        cache.set(key, entities)
    return entities

def get_choice(value, _type=str, deli=','):
    '''
    Used to clean a form field where multiple\n
    choices are seperated using a delimiter such as comma.\n
    Removing the empty value.
    '''
    try:
        results = value.split(deli)
        return [_type(r.strip()) for r in results if r]
    except Exception, e:
        raise forms.ValidationError(str(e))

class QueryCriteria(object):

    PRIORITIES = {
        'plan': (
            'pl_id', 'pl_summary', 'pl_authors',  'p_product', 'pl_type',
            'pl_active', 'pl_created_since', 'pl_created_before',  'pl_tags'),
        'case': (
            'cs_id', 'cs_summary', 'cs_authors', 'cs_tester', 'cs_tags', 'cs_bugs', 'cs_script',
            'cs_status', 'cs_auto', 'cs_proposed', 'cs_priority', 'cs_created_since',
            'cs_created_before', 'p_version', 'p_component', 'p_category'),
        'run': (
            'r_id','r_summary', 'r_manager', 'r_tester', 'r_running',
            'r_tags', 'r_created_since', 'r_created_before', 'p_product',)
    }

    RULES = {
        'plan': {
            'pl_id': 'plan_id__in',
            'pl_summary': 'summary__startswith',
            'pl_type': 'type__in',
            'pl_authors': 'author__in',
            'pl_tags': 'tags__in',
            'pl_active': 'is_active',
            'pl_created_since': 'create_date__gte',
            'pl_created_before': 'create_date__lte',
            'p_product': 'product__in',
        },
        'product': {
            'p_product': 'product__in',
            'p_version': 'version__in',
            'p_component': 'component__in',
            'p_category': 'category__in',
            'p_build': 'build__in',
        },
        'case': {
            'cs_id': 'case_id',
            'cs_summary': 'summary__startswith',
            'cs_authors': 'author__in',
            'cs_tester': 'tester__in',
            'cs_tags': 'tags__in',
            'cs_bugs': 'bugs__in',
            'cs_status': 'status__in',
            'cs_auto': 'is_automated',
            'cs_proposed': 'is_auto_prop',
            'cs_priority': 'priority__in',
            'cs_script': 'script__startswith',
            'cs_created_since': 'create_date__gte',
            'cs_created_before': 'create_date__lte',
            'p_version': 'version__in',
            'p_component': 'components__in',
            'p_category': 'category__in',
        },
        'run': {
            'r_id': 'run_id',
            'r_summary': 'summary__startswith',
            'r_manager': 'manager__username__in',
            'r_tester': 'tester__username__in',
            'r_running': 'is_finished',
            'r_tags': 'tag__name__in',
            'r_created_since': 'create_date__gte',
            'r_created_before': 'create_date__lte',
            'p_product': 'product__in',
        }
    }

    def __init__(self, queryset, queries, result_kls):
        self.queryset   = queryset
        self.queries    = queries
        self.result_kls = result_kls

    def filter(self):
        queryset = None
        rules = self.RULES[self.result_kls]
        for key in self.PRIORITIES[self.result_kls]:
            if not rules.has_key(key):
                continue
            value   = self.queries.get(key, None)
            if value:
                print 'applying filter %s : %s' %(key, value)
                qs = queryset or self.queryset
                queryset = qs.filter(**{rules[key]: value})
        return queryset

class PlanForm(forms.Form):
    PLAN_TYPE_CHOICES = [
        (t.pk, t.name) for t in cached_entities('TestPlanType')
    ]
    pl_type     = LooseIF()
    pl_summary  = LooseCF(max_length=50)
    pl_id       = LooseCF()
    pl_authors  = LooseCF(max_length=100)
    pl_tags     = LooseCF(max_length=100)
    pl_active   = forms.BooleanField(required=False)
    pl_created_since  = LooseDF()
    pl_created_before = LooseDF()

    def clean_pl_id(self):
        return get_choice(self.cleaned_data['pl_id'], _type=int)

    def clean_pl_tags(self):
        return get_choice(self.cleaned_data['pl_tags'])

    def clean_pl_authors(self):
        return get_choice(self.cleaned_data['pl_authors'])

class CaseForm(forms.Form):
    STATUS_CHOICE = [
        (s.pk, s.name) for s in cached_entities('TestCaseStatus')
    ]
    PRIORITY_CHOICE = [
        (p.pk, p.value) for p in cached_entities('Priority')
    ]
    cs_id       = forms.IntegerField(required=False)
    cs_summary  = LooseCF(max_length=100)
    cs_authors  = LooseCF(max_length=100)
    cs_tester   = LooseCF(max_length=30)
    cs_tags     = LooseCF(max_length=100)
    cs_bugs     = LooseCF(max_length=100)
    cs_status   = forms.MultipleChoiceField(
                    required=False,
                    choices=STATUS_CHOICE)
    cs_priority = forms.MultipleChoiceField(
                    required=False,
                    choices=PRIORITY_CHOICE)
    cs_auto     = forms.BooleanField(required=False)
    cs_proposed = forms.BooleanField(required=False)
    cs_script   = LooseCF(max_length=200)
    cs_created_since  = LooseDF()
    cs_created_before = LooseDF()

    def clean_cs_authors(self):
        return get_choice(self.cleaned_data['cs_authors'])

    def clean_cs_bugs(self):
        return get_choice(self.cleaned_data['cs_bugs'], int)

    def clean_cs_tags(self):
        return get_choice(self.cleaned_data['cs_tags'])

class RunForm(forms.Form):
    r_id        = forms.IntegerField(required=False)
    r_summary   = LooseCF(max_length=100)
    r_manager   = LooseCF(max_length=30)
    r_tester    = LooseCF(max_length=30)
    r_tags      = LooseCF(max_length=10)
    r_running   = forms.BooleanField(required=False)
    r_begin     = LooseDF()
    r_finished  = LooseDF()
    r_created_since  = LooseDF()
    r_created_before = LooseDF()

def get_prod_queries(data):
    def _get(key):
        values = data.getlist(key)
        return [v for v in values if v]
    p_product   = _get('p_product')
    p_version   = _get('p_version')
    p_component = _get('p_component')
    p_build     = _get('p_build')
    p_category  = _get('p_category')
    return locals()

def advance_search(request, tmpl='search/advanced_search.html'):
    data        = request.GET
    target      = data.get('target')
    prod_query  = get_prod_queries(data)
    plan_form   = PlanForm(data)
    case_form   = CaseForm(data)
    run_form    = RunForm(data)
    if not data:
        PRODUCT_CHOICE = [
            (p.pk, p.name) for p in cached_entities('product')
        ]
        return direct_to_template(request, tmpl, locals())
    # DEBUG:
    if settings.DEBUG:
        print 'plan_form valid?', plan_form.is_valid() and plan_form.cleaned_data
        print 'case_form valid?', case_form.is_valid() and case_form.cleaned_data
        print 'run_form valid?', run_form.is_valid() and run_form.cleaned_data
    all_forms   = (plan_form, case_form, run_form)
    form_err    = [f.errors for f in all_forms if not f.is_valid()]
    if form_err:
        print 'Ooops'
        return HttpResponse(str(form_err))

    plans   = build_queryset(plan_form.cleaned_data, target, 'plan', prod_query)
    runs    = build_queryset(run_form.cleaned_data, target, 'run', prod_query)
    cases   = build_queryset(case_form.cleaned_data, target, 'case', prod_query)

    start = time.time()
    results = sum_queried_results(plans, runs, cases, target)
    end = time.time()
    timecost = round(end - start, 3)
    return HttpResponse('Time used: ' + str(timecost) + '<br/>' + str(results))

def build_queryset(target_queries, target, result_kls, prod_queries=None):
    klasses = {
        'plan': TestPlan,
        'case': TestCase,
        'run': TestRun
    }
    sq = SearchQuerySet().models(klasses[result_kls])
    target_queries.update(prod_queries)
    qc = QueryCriteria(sq, target_queries, result_kls)
    qc = qc.filter()
    return qc

def evaluate_queryset(queryset, target, ctype):
    attr_map = {
        'testplan': {
            'plan': 'plan_id',
            'case': 'case_ids',
            'run': 'run_ids',
         },
        'testcase': {
            'plan': 'plan_ids',
            'case': 'case_id',
            'run': 'run_ids',
        },
        'testrun': {
            'plan': 'plan',
            'case': 'case_ids',
            'run': 'run_id'
        }
    }
    attr = attr_map[ctype][target]
    print 'getting %s from %s and attr is: %s' % (target, ctype, attr)
    for hit in queryset:
        val = getattr(hit, attr)
        yield val

def serialize_queries(docs):
    for key in docs:
        if not key: continue
        if isinstance(key, str):
            ids = key.split()
            for _id in ids:
                yield int(_id)
        else:
            yield key

def sum_queried_results(plans, runs, cases, target):
    result = []
    if plans is not None:
        print 'plans count:', plans.count()
        keys = evaluate_queryset(plans, target, 'testplan')
        result.append(set(serialize_queries(keys)))

    if runs is not None:
        print 'runs count:', runs.count()
        keys = evaluate_queryset(runs, target, 'testrun')
        result.append(set(serialize_queries(keys)))

    if cases is not None:
        print 'cases count:', cases.count()
        keys = evaluate_queryset(cases, target, 'testcase')
        result.append(set(serialize_queries(keys)))

    if result:
        return set.intersection(*result)
    else:
        return None

if __name__ == '__main__':
    import doctest
    doctest.testmod()
