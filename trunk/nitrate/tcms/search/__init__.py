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
from django.core.cache import cache
from django.db.models.query import QuerySet

# from tcms
from tcms.testplans.models import TestPlan, TestPlanType
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestRun
from tcms.management.models import Product, Version, Priority
from tcms.search.query import CONTENT_TYPES, SmartDjangoQuery
from tcms.search.forms import CaseForm, RunForm, PlanForm
from tcms.core.helpers.cache import cached_entities

# from stdlib
from datetime import datetime
import time

def advance_search(request, tmpl='search/advanced_search.html'):
    '''
    View of /advance-search/
    '''
    errors      = None
    data        = request.GET
    target      = data.get('target')
    plan_form   = PlanForm(data)
    case_form   = CaseForm(data)
    run_form    = RunForm(data)
    # Update MultipleModelChoiceField on each form dynamically
    plan_form.populate(data)
    case_form.populate(data)
    run_form.populate(data)
    all_forms   = (plan_form, case_form, run_form)
    errors      = [f.errors for f in all_forms if not f.is_valid()]
    if errors or not data:
        PRODUCT_CHOICE = [
            (p.pk, p.name) for p in cached_entities('product')
        ]
        PLAN_TYPE_CHOICES = cached_entities('testplantype')
        errors = fmt_errors(errors)
        return direct_to_template(request, tmpl, locals())

    start = time.time()
    results = retrieve_results(request, plan_form.cleaned_data,
        run_form.cleaned_data, case_form.cleaned_data, target)
    end = time.time()
    timecost = round(end - start, 3)
    queries = fmt_queries(*[f.cleaned_data for f in all_forms])
    queries['Target'] = target
    return render_results(request, results, timecost, queries)

def retrieve_results(request, plan_query, run_query, case_query, target):
    '''
    Try hitting the cache on first attempt.\n
    Hits index on empty values.
    '''
    from hashlib import md5
    key     = remove_from_request_path(request, 'page')
    key     = md5(key).hexdigest()
    results = cache.get(key)
    if not results:
        results = query(plan_query, run_query, case_query, target)
        cache.set(key, results)
    return results

def query(plan_query, run_query, case_query, target, using='orm'):
    USING = {
        'orm': {
            'query': SmartDjangoQuery,
            'sum': sum_orm_queries
        }
    }
    Query   = USING[using]['query']
    Sum     = USING[using]['sum']
    plans   = Query(plan_query, 'plan', target)
    runs    = Query(run_query, 'run', target)
    cases   = Query(case_query, 'case', target)
    results = Sum(plans, cases, runs, target)
    return results

def sum_orm_queries(plans, cases, runs, target):
    plans = plans.evaluate()
    cases = cases.evaluate()
    runs  = runs.evaluate()
    if target == 'run':
        if runs is None: runs = TestRun.objects.all()
        if cases: runs = runs.filter(case_run__case__in=cases)
        if plans: runs = runs.filter(plan__in=plans)
        return runs
    if target == 'plan':
        if plans is None: plans = TestPlan.objects.all()
        if cases: plans = plans.filter(case__in=cases)
        if runs:  plans = plans.filter(run__in=runs)
        return plans
    if target == 'case':
        if cases is None: cases = TestCase.objects.all()
        if runs:  cases = cases.filter(case_run__run__in=runs)
        if plans: cases = cases.filter(plan__in=plans)
        return cases

def render_results(request, results, time_cost, queries, tmpl='search/results.html'):
    '''
    Using a SQL "in" query and PKs as the arguments.
    '''
    klasses = {
        'plan': {'class': TestPlan, 'result_key': 'test_plans'},
        'case': {'class': TestCase, 'result_key': 'test_cases'},
        'run': {'class': TestRun, 'result_key': 'test_runs'}
    }
    if results is None:
        qs      = klasses[request.GET['target']]['class']._default_manager.none()
    else:
        qs      = klasses[request.GET['target']]['class']._default_manager.filter(pk__in=results)
    return direct_to_template(request, tmpl,
        {
            klasses[request.GET['target']]['result_key']: qs,
            'time_cost': time_cost,
            'queries': queries
        }
    )

def remove_from_request_path(request, name):
    '''
    Remove a parameter from request.get_full_path()\n
    and return the modified path afterwards.
    '''
    path = request.get_full_path().split('?')[1].split('&')
    path = [p for p in path if not p.startswith(name)]
    path = '&'.join(path)
    return path

def fmt_errors(form_errors):
    '''
    Format errors collected in a Django Form
    for a better appearance.
    '''
    errors = []
    for error in form_errors:
        for k, v in error.iteritems():
            k = k.replace('p_product', 'product').replace('p_', 'product ').replace('cs_', 'case ')\
            .replace('pl_', 'plan ').replace('r_', 'run ').replace('_', ' ')
            if isinstance(v, list):
                v = ', '.join(map(str, v))
            errors.append((k, v))
    return errors

def fmt_queries(*queries):
    '''
    Format the queries string.
    '''
    results = {}
    for query in queries:
        for k, v in query.iteritems():
            k = k.replace('p_product', 'product').replace('p_', 'product ').replace('cs_', 'case ')\
            .replace('pl_', 'plan ').replace('r_', 'run ').replace('_', ' ')
            if v:
                if isinstance(v, QuerySet):
                    try:
                        v = ', '.join([o.name for o in v])
                    except AttributeError:
                        v = ', '.join([o.value for o in v])
                if isinstance(v, list):
                    v = ', '.join(map(str, v))
                results[k] = v
    return results

if __name__ == '__main__':
    import doctest
    doctest.testmod()
