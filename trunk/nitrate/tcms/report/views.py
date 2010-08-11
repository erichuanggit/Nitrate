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
#   Xuqing Kuang <xkuang@redhat.com>

from django.db import connection, transaction
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from tcms.management.models import Classification, Product
from tcms.core.utils.counter import CaseRunStatusCounter, RunsCounter
from tcms.core.utils.raw_sql import ReportSQL as RawSQL

MODULE_NAME = "report"

def overall(request, template_name='report/list.html'):
    """Overall of products report"""
    SUB_MODULE_NAME = 'overall'
    products = Product.objects.all()
    
    products = products.extra(select={
        'plans_count': RawSQL.index_product_plans_count,
        'runs_count': RawSQL.index_product_runs_count,
        'cases_count': RawSQL.index_product_cases_count,
    })
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'products': products
    })
    
def overview(request, product_id, template_name='report/overview.html'):
    """Product for a product"""
    SUB_MODULE_NAME = 'overview'
    
    try:
        product = Product.objects.get(id = product_id)
    except Product.DoesNotExist, error:
        raise Http404(error)
    
    cursor = connection.cursor()
    cursor.execute(RawSQL.overview_runing_runs_count, [product.id])
    rows = cursor.fetchall()
    
    if len(rows) == 2:
        runs_count = RunsCounter(rows[0][1], rows[1][1])
    else:
        runs_count = RunsCounter()
        
        for row in rows:
            setattr(runs_count, row[0], row[1])
        
    cursor.execute(RawSQL.overview_case_runs_count, [product.id])
    rows = cursor.fetchall()
    
    total = 0
    for row in rows:
        if row[0]:
            total += row[1]
    
    case_run_counter = CaseRunStatusCounter([])
    for row in rows:
        if row[0]:
            setattr(case_run_counter, row[0], row[1])
            setattr(case_run_counter, row[0] + '_percent', float(row[1]) / total * 100)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'product': product,
        'runs_count': runs_count,
        'case_run_count': case_run_counter,
    })
    
def version(request, product_id, template_name='report/version.html'):
    """Version report for a product"""
    SUB_MODULE_NAME = 'version'
    
    try:
        product = Product.objects.get(id = product_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    versions = product.version.all()
    versions = versions.extra(select={
        'plans_count': RawSQL.version_plans_count,
        'running_runs_count': RawSQL.version_running_runs_count,
        'finished_runs_count': RawSQL.version_finished_runs_count,
        'cases_count': RawSQL.version_cases_count,
        'case_run_percent': RawSQL.version_case_run_percent,
        'failed_case_runs_count': RawSQL.version_failed_case_runs_count,
    })
    
    case_run_counter = None
    current_version = None
    if request.REQUEST.get('version_id'):
        try:
            current_version = product.version.get(id = request.REQUEST['version_id'])
        except ObjectDoesNotExist, error:
            raise Http404(error)
        
        cursor = connection.cursor()
        cursor.execute(RawSQL.version_case_runs_count, [
            product.id,
            current_version.value,
        ])
        rows = cursor.fetchall()
        total = 0
        for row in rows:
            if row[0]:
                total += row[1]
        
        case_run_counter = CaseRunStatusCounter([])
        for row in rows:
            if row[0]:
                setattr(case_run_counter, row[0], row[1])
                setattr(case_run_counter, row[0] + '_percent', float(row[1]) / total * 100)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'product': product,
        'versions': versions,
        'version': current_version,
        'case_run_count': case_run_counter,
    })
    
def build(request, product_id, template_name='report/build.html'):
    """Build report for a product"""
    SUB_MODULE_NAME = 'build'
    
    try:
        product = Product.objects.get(id = product_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    builds = product.build.all()
    builds = builds.extra(select={
        'total_runs': RawSQL.build_total_runs,
        'finished_runs': RawSQL.build_finished_runs,
        'finished_case_run_percent': RawSQL.build_finished_case_runs_percent,
        'failed_case_run_count': RawSQL.build_failed_case_run_count,
    })
    
    case_run_counter = None
    current_build = None
    if request.REQUEST.get('build_id'):
        try:
            current_build = product.build.get(build_id = request.REQUEST['build_id'])
        except ObjectDoesNotExist, error:
            raise Http404(error)
        
        cursor = connection.cursor()
        cursor.execute(RawSQL.build_case_runs_count, [current_build.build_id, ])
        rows = cursor.fetchall()
        total = 0
        for row in rows:
            if row[0]:
                total += row[1]
        
        case_run_counter = CaseRunStatusCounter([])
        for row in rows:
            if row[0]:
                setattr(case_run_counter, row[0], row[1])
                setattr(case_run_counter, row[0] + '_percent', float(row[1]) / total * 100)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'product': product,
        'builds': builds,
        'build': current_build,
        'case_run_count': case_run_counter
    })
    
def component(request, product_id, template_name='report/component.html'):
    """Component report for a product"""
    SUB_MODULE_NAME = 'component'
    
    try:
        product = Product.objects.get(id = product_id)
    except Product.DoesNotExist, error:
        raise Http404(error)
    
    components = product.component.all()
    components = components.extra(select={
        'total_cases': RawSQL.component_total_cases,
        'finished_case_run_percent': RawSQL.component_finished_case_run_percent,
        'failed_case_run_count': RawSQL.component_failed_case_run_count,
    })
    
    case_run_counter = None
    current_component = None
    if request.REQUEST.get('component_id'):
        try:
            current_component = product.component.get(id = request.REQUEST['component_id'])
        except ObjectDoesNotExist, error:
            raise Http404(error)
        
        cursor = connection.cursor()
        cursor.execute(RawSQL.component_case_runs_count, [current_component.id, ])
        rows = cursor.fetchall()
        total = 0
        for row in rows:
            if row[0]:
                total += row[1]
        
        case_run_counter = CaseRunStatusCounter([])
        for row in rows:
            if row[0]:
                setattr(case_run_counter, row[0], row[1])
                setattr(case_run_counter, row[0] + '_percent', float(row[1]) / total * 100)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'product': product,
        'components': components,
        'component': current_component,
        'case_run_count': case_run_counter
    })

def custom_search(request, template_name='report/custom_search.html'):
    """Custom report with search function"""
    from tcms.management.models import TestBuild
    from forms import CustomSearchForm
    
    SUB_MODULE_NAME = 'custom_search'
    from pprint import pprint
    def calc_percent(x, y):
        pprint([x, y])
        if not x or not y:
            return 0
        
        return float(x)/y*100
    
    if request.REQUEST.get('a') == 'search':
        form = CustomSearchForm(request.REQUEST)
        form.populate(product_id = request.REQUEST.get('product'))
        if form.is_valid():
            tbs = TestBuild.objects
            for k, v in form.fields.items():
                if form.cleaned_data[k]:
                    tbs = tbs.filter(**{k: form.cleaned_data[k]})
            
            tbs = tbs.extra(select={
                'plans_count': RawSQL.custom_search_plans_count,
                'runs_count': RawSQL.custom_search_runs_count,
                'case_runs_count': RawSQL.custom_search_case_runs_count,
                'case_runs_passed_count': RawSQL.custom_search_case_runs_passed_count,
                'case_runs_failed_count': RawSQL.custom_search_case_runs_failed_count,
            })
            
            tbs = tbs.distinct()
        else:
            tbs = TestBuild.objects.none()
    else:
        form = CustomSearchForm()
        tbs = TestBuild.objects.none()
    
    for tb in tbs:
        tb.case_runs_passed_percent = calc_percent(tb.case_runs_passed_count, tb.case_runs_count)
        tb.case_runs_failed_percent = calc_percent(tb.case_runs_failed_count, tb.case_runs_count)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form': form,
        'builds': tbs,
    })

def custom_details(request, template_name='report/custom_details.html'):
    """Custom report with search function"""
    from tcms.testplans.models import TestPlan
    from tcms.testruns.models import TestCaseRun, TestCaseRunStatus, TestRun
    from forms import CustomSearchDetailsForm
    from pprint import pprint
    SUB_MODULE_NAME = 'custom_search'
    
    form = CustomSearchDetailsForm(request.REQUEST)
    form.populate(product_id = request.REQUEST.get('product'))
    if form.is_valid():
        tcrses = TestCaseRunStatus.objects.all()
        
        tps = TestPlan.objects
        trs = TestRun.objects
        tcrs = TestCaseRun.objects.select_related('case', 'case_run_status', 'tested_by')
        
        if form.cleaned_data['product']:
            tps = tps.filter(run__build__product = form.cleaned_data['product'])
            trs = trs.filter(build__product = form.cleaned_data['product'])
            tcrs = tcrs.filter(run__build__product = form.cleaned_data['product'])
            
        if form.cleaned_data['build_run__product_version']:
            tps = tps.filter(run__product_version = form.cleaned_data['build_run__product_version'])
            trs = trs.filter(product_version = form.cleaned_data['build_run__product_version'])
            tcrs = tcrs.filter(run__product_version = form.cleaned_data['build_run__product_version'])
            
        if form.cleaned_data['pk__in']:
            tps = tps.filter(run__build = form.cleaned_data['pk__in'])
            trs = trs.filter(build = form.cleaned_data['pk__in'])
            tcrs = tcrs.filter(run__build = form.cleaned_data['pk__in'])
        
        tps = tps.distinct()
        trs = trs.filter(plan__in = tps).distinct()
        tcrs = tcrs.distinct()
        
        for tp in tps:
            tp.runs = []
            
            for tr in trs:
                if tp.plan_id == tr.plan_id:
                    tp.runs.append(tr)
        
        cursor = connection.cursor()
        for tr in trs:
            cursor.execute(RawSQL.custom_details_case_run_count % tr.pk)
            for s, n in cursor.fetchall():
                setattr(tr, s, n)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form': form,
        'test_plans': tps,
        'test_runs': trs,
        'test_case_runs': tcrs,
        'test_case_run_status': tcrses,
    })
