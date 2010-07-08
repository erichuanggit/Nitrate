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

from datetime import datetime, timedelta

from django.contrib.auth.decorators import user_passes_test
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson

from tcms.core import forms
from tcms.core.utils import Prompt

from models import TestCase, TestCaseStatus

MODULE_NAME = "testcases"


@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def automated(request):
    """
    Change the automated status for cases

    Parameters:
    - a: Actions
    - case: IDs for case_id
    - o_is_automated: Status for is_automated
    - o_is_automated_proposed: Status for is_automated_proposed

    Returns:
    - Serialized JSON
    """
    from forms import CaseAutomatedForm
    
    ajax_response = {'rc': 0, 'response': 'ok'}
    
    if request.method == 'POST':
        form = CaseAutomatedForm(request.REQUEST)
        #form.populate()
        if form.is_valid():
            tcs = TestCase.objects.filter(
                pk__in = request.REQUEST.getlist('case')
            )
            
            if form.cleaned_data['a'] == 'change':
                if isinstance(form.cleaned_data['is_automated'], int):
                    tcs.update(is_automated = form.cleaned_data['is_automated'])
                
                if isinstance(form.cleaned_data['is_automated_proposed'], bool):
                    tcs.update(
                        is_automated_proposed = form.cleaned_data['is_automated_proposed']
                    )
        else:
            ajax_response['rc'] = 1
            ajax_response['response'] = forms.errors_to_list(form)
    
    return HttpResponse(simplejson.dumps(ajax_response))

@user_passes_test(lambda u: u.has_perm('testcases.add_testcase'))
def new(request, template_name = 'case/new.html'):
    from tcms.testplans.models import TestPlan
    from forms import NewCaseForm
    
    if request.REQUEST.get('from_plan'):
        try:
            tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
        except ObjectDoesNotExist, error:
            tp = None
    else:
        tp = None
    
    # Initial the form parameters
    if tp:
        default_form_parameters = {
            'product': tp.product_id,
            'component': tp.component.defer('id').values_list('pk', flat = True),
            'is_automated': '0',
        }
    else:
        default_form_parameters = { 'is_automated': '0' }
    
    if request.method == "POST":
        form = NewCaseForm(request.REQUEST)
        if request.REQUEST.get('product'):
            form.populate(product_id = request.REQUEST['product'])
        else:
            form.populate()
        
        if form.is_valid():
            try:
                tc = TestCase.create(
                    author = request.user,
                    values = form.cleaned_data
                )
                
                tc.add_text(
                    case_text_version = 1,
                    author = request.user,
                    action = form.cleaned_data['action'],
                    effect = form.cleaned_data['effect'],
                    setup = form.cleaned_data['setup'],
                    breakdown = form.cleaned_data['breakdown'],
                )
                
                # Add test tags to the case
                #if request.user.has_perm('testcases.add_testcasetag'):
                #    for tag in form.cleaned_data['tag']:
                #        tc.add_tag(
                #            tag = tag
                #        )
                
                # Assign the case to the plan
                if tp:
                    tc.add_to_plan(plan = tp)
                
                # Add components into the case
                for component in form.cleaned_data['component']:
                    tc.add_component(component = component)
            except:
                raise
            
            class ReturnActions(object):
                def __init__(self, case, plan):
                    self.__all__ = ('_addanother', '_continue', '_returntocase', '_returntoplan')
                    self.case = case
                    self.plan = plan
                
                def _continue(self):
                    if self.plan:
                        return HttpResponseRedirect('%s?from_plan=%s' % (
                                reverse('tcms.testcases.views.edit', args=[self.case.case_id, ]),
                                self.plan.plan_id
                            )
                        )
                        
                    return HttpResponseRedirect(
                        reverse('tcms.testcases.views.edit', args=[tc.case_id, ]),
                    )
                
                def _addanother(self):
                    form = NewCaseForm(initial=default_form_parameters)
                    
                    if tp:
                        form.populate(product_id = self.plan.product_id)
                    
                    return form
                
                def _returntocase(self):
                    if self.plan:
                        return HttpResponseRedirect('%s?from_plan=%s' % (
                                reverse('tcms.testcases.views.get', args=[self.case.pk, ]),
                                self.plan.plan_id
                            )
                        )
                    
                    return HttpResponseRedirect(
                        reverse('tcms.testcases.views.get', args=[self.case.pk, ]),
                    )
                
                def _returntoplan(self):
                    if not self.plan:
                        raise Http404
                    
                    return HttpResponseRedirect(
                        reverse('tcms.testplans.views.get', args=[self.plan.pk, ]),
                    )
            
            # Genrate the instance of actions
            ras = ReturnActions(case = tc, plan = tp)
            for ra_str in ras.__all__:
                if request.REQUEST.get(ra_str):
                    func = getattr(ras, ra_str)
                    break
            else:
                func = ras._returntocase
            
            # Get the function and return back
            result = func()
            if isinstance(result, HttpResponseRedirect):
                return result
            else:
                # Assume here is the form
                form = result
    else:
        try:
            tp = TestPlan.objects.get(plan_id = request.REQUEST.get('from_plan'))
        except ObjectDoesNotExist, error:
            tp = None
        
        form = NewCaseForm(initial=default_form_parameters)
        if tp:
            form.populate(product_id = tp.product_id)
    
    return direct_to_template(request, template_name, {
        'test_plan': tp,
        'form': form
    })

def all(request, template_name="case/all.html"):
    """
    Generate the case list in search case and case zone in plan
    
    Parameters:
    a: Action
       -- search: Search form submitted.
       -- initial: Initial the case filter
    from_plan: Plan ID
       -- [number]: When the plan ID defined, it will build the case page in plan
    """
    from forms import SearchCaseForm, CaseFilterForm
    from tcms.testplans.forms import ImportCasesViaXMLForm
    
    from tcms.core.utils.raw_sql import RawSQL
    from tcms.testplans.models import TestPlan
    from tcms.management.models import Priority, TestTag
    
    
    # Intial the plan in plan details page
    if request.REQUEST.get('from_plan'):
        tp = TestPlan.objects.get(pk = request.REQUEST['from_plan'])
    else:
        tp = TestPlan.objects.none()
    
    # Initial the form and template
    d_status = TestCaseStatus.objects.exclude(name = 'DISABLED')
    d_status_ids = d_status.values_list('pk', flat=True)
    
    if request.REQUEST.get('from_plan'):
        template_name = 'plan/get_cases.html'
        SearchForm = CaseFilterForm
    else:
        SearchForm = SearchCaseForm
    
    if request.REQUEST.get('a') in ('search', 'sort'):
        search_form = SearchForm(request.REQUEST)
    else:
        search_form = SearchForm(initial={
            'case_status': d_status_ids
        })
    
    # Populate the form
    if request.REQUEST.get('product'):
        search_form.populate(product_id = request.REQUEST['product'])
    elif tp and tp.product_id:
        search_form.populate(product_id = tp.product_id)
    else:
        search_form.populate()
    
    # Query the database when search
    if request.REQUEST.get('a') in ('search', 'sort') and search_form.is_valid():
        tcs = TestCase.list(search_form.cleaned_data)
    elif request.REQUEST.get('a') == 'initial':
        tcs = TestCase.objects.filter(case_status__in = d_status)
    else:
        tcs = TestCase.objects.none()
    
    # Search the relationship
    if tp:
        tcs = tcs.filter(plan = tp)
    
    tcs = tcs.select_related(
        'author', 'default_tester', 'case_status',
        'priority', 'category'
    )
    
    tcs = tcs.extra(select={
        'num_bug': RawSQL.num_case_bugs,
    })
    
    tcs = tcs.distinct()
    
    # Resort the order
    if request.REQUEST.get('case_sort_by'):
        tcs = tcs.order_by(
            request.REQUEST.get('case_sort_by')
        )
    
    # Initial the case ids
    if request.REQUEST.get('case'):
        selected_case_ids = map(lambda f: int(f), request.REQUEST.getlist('case'))
    else:
        selected_case_ids = tcs.values_list('pk', flat = True)
    
    # Get the tags own by the cases
    if tp:
        ttags = TestTag.objects.filter(testcase__in = tp.case.all()).distinct()
    else:
        ttags = TestTag.objects.filter(testcase__in = tcs).distinct()
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'test_cases': tcs,
        'test_plan': tp,
        'search_form': search_form,
        'xml_form': ImportCasesViaXMLForm(initial = {'a': 'import_cases'}),
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
        'priorities': Priority.objects.all(),
        'case_own_tags': ttags,
    })

def get(request, case_id, template_name = 'case/get.html'):
    from tcms.core.utils.raw_sql import RawSQL
    try:
        tc = TestCase.objects.select_related(
            'author', 'default_tester', 'category__name',
            'category__product__name', 'priority__name', 'case_status__name'
        ).get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    if request.GET.get('from_plan'):
        from tcms.testplans.models import TestPlan
        tp = TestPlan.objects.select_related().get(
            plan_id = request.GET.get('from_plan')
        )
    else:
        tp = None
        
    tps = tc.plan.select_related().all()
    tcrs = tc.case_run.select_related(
        'run__summary', 'tested_by', 'assignee', 'case__category__name',
        'case__priority__name', 'case_run_status__name'
    ).all()
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    })
    
    tc.latest_text = tc.latest_text()
    
    return direct_to_template(request, template_name, {
        'test_case': tc,
        'test_plan': tp,
        'test_plans': tps,
        'test_case_runs': tcrs,
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
    })

def get_details(request, case_id, template_name = 'case/get_details.html'):
    """Get the case text with selected case text version"""
    from tcms.testruns.models import TestCaseRun
    
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    if request.REQUEST.get('case_run_id'):
        tcr = TestCaseRun.objects.get(case_run_id = request.REQUEST['case_run_id'])
        bugs = tcr.get_bugs()
    else:
        tcr = None
        bugs = tc.get_bugs()
    
    if request.REQUEST.get('case_text_version') and request.REQUEST['case_text_version']:
        try:
            case_text = tc.text.get(case_text_version = request.REQUEST['case_text_version'])
        except ObjectDoesNotExist:
            case_text = tc.latest_text()
    else:
        case_text = tc.latest_text()
    
    return direct_to_template(request, template_name, {
        'test_case': tc,
        'test_case_run': tcr,
        'bugs': bugs,
        'case_text': case_text
    })

@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def edit(request, case_id, template_name = 'case/edit.html'):
    from forms import EditCaseForm
    
    try:
        tc = TestCase.objects.select_related().get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    if request.REQUEST.get('from_plan'):
        from tcms.testplans.models import TestPlan
        tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
    else:
        tp = None
    
    # If the form is submitted
    if request.method == "POST":
        form = EditCaseForm(request.REQUEST)
        if request.REQUEST.get('product'):
            form.populate(product_id = request.REQUEST['product'])
        elif tp:
            form.populate(product_id = tp.product_id)
        else:
            form.populate()
        
        # Check the form and modify the case
        if form.is_valid():
            if tc.summary != form.cleaned_data['summary']:
                tc.log_action(request.user, 'Case summary changed from %s to %s in edit page.' % (
                    tc.summary, form.cleaned_data['summary']
                ))
                tc.summary = form.cleaned_data['summary']
            
            if tc.case_status != form.cleaned_data['case_status']:
                tc.log_action(request.user, 'Case status changed from %s to %s in edit page.' % (
                    tc.case_status, form.cleaned_data['case_status']
                ))
                tc.case_status = form.cleaned_data['case_status']
            
            if tc.category != form.cleaned_data['category']:
                tc.log_action(request.user, 'Case category changed from %s to %s in edit page.' % (
                    tc.category, form.cleaned_data['category']
                ))
                tc.category = form.cleaned_data['category']
            
            if tc.priority != form.cleaned_data['priority']:
                tc.log_action(request.user, 'Case priority changed from %s to %s in edit page.' % (
                    tc.priority, form.cleaned_data['priority']
                ))
                tc.priority = form.cleaned_data['priority']
            
            if tc.notes != form.cleaned_data['notes']:
                tc.log_action(request.user, 'Case notes changed from %s to %s in edit page.' % (
                    tc.notes, form.cleaned_data['notes']
                ))
                tc.notes = form.cleaned_data['notes']
            
            if not tc.default_tester_id or tc.default_tester != form.cleaned_data['default_tester']:
                tc.log_action(request.user, 'Case default tester changed from %s to %s in edit page.' % (
                    tc.default_tester_id and tc.default_tester, form.cleaned_data['default_tester']
                ))
                tc.default_tester = form.cleaned_data['default_tester']
            
            # FIXME: Buggy here, timedelta from form cleaned data need to convert.
            #if tc.estimated_time != form.cleaned_data['estimated_time']:
            #    tc.log_action(request.user, 'Case estimated time changed from %s to %s in edit page.' % (
            #        tc.estimated_time, form.cleaned_data['estimated_time']
            #    ))
            tc.estimated_time = form.cleaned_data['estimated_time']
            
            tc.is_automated = form.cleaned_data['is_automated']
            tc.is_automated_proposed = form.cleaned_data['is_automated_proposed']
            tc.script = form.cleaned_data['script']
            tc.arguments = form.cleaned_data['arguments']
            tc.reqirement = form.cleaned_data['requirement']
            tc.alias = form.cleaned_data['alias']
            tc.save()
            
            tc.add_text(
                author = request.user,
                create_date = datetime.now(),
                action = form.cleaned_data.get('action'),
                effect = form.cleaned_data.get('effect'),
                setup = form.cleaned_data.get('setup'),
                breakdown = form.cleaned_data.get('breakdown')
            )
            
            # Remove old case component
            tc.clear_components()
            
            # Add components into the case
            for component in form.cleaned_data['component']:
                tc.add_component(component = component)
            
            if request.REQUEST.get('_continue'):
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('tcms.testcases.views.edit', args=[case_id, ]),
                    request.REQUEST.get('from_plan', None),
                ))
            
            if request.REQUEST.get('_continuenext'):
                if not tp:
                    raise Http404
                
                # Exclude the disabled cases
                pk_list = tp.case.exclude(case_status__name = 'DISABLED')
                pk_list = pk_list.defer('case_id').values_list('pk', flat=True)
                
                # Get the previous and next case
                p_tc, n_tc = tc.get_previous_and_next(pk_list = pk_list)
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('tcms.testcases.views.edit', args=[n_tc.pk, ]),
                    tp.pk,
                ))
            
            return HttpResponseRedirect('%s?from_plan=%s' % (
                reverse('tcms.testcases.views.get', args=[case_id, ]),
                request.REQUEST.get('from_plan', None),
            ))
    else:
        tctxt = tc.latest_text()
        form = EditCaseForm(initial={
            'summary': tc.summary,
            'default_tester': tc.default_tester_id and tc.default_tester.email or None,
            'requirement': tc.requirement,
            'is_automated': tc.get_is_automated_form_value(),
            'is_automated_proposed': tc.is_automated_proposed,
            'script': tc.script,
            'arguments': tc.arguments,
            'alias': tc.alias,
            'case_status': tc.case_status_id,
            'priority': tc.priority_id,
            'product': tc.category.product_id,
            'category': tc.category_id,
            'notes': tc.notes,
            'component': [c.pk for c in tc.component.all()],
            'estimated_time': tc.estimated_time,
            'setup': tctxt.setup,
            'action': tctxt.action,
            'effect': tctxt.effect,
            'breakdown': tctxt.breakdown,
        })
        
        form.populate(product_id = tc.category.product_id)
    
    return direct_to_template(request, template_name, {
        'test_case': tc,
        'test_plan': tp,
        'form': form,
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
    })

def text_history(request, case_id, template_name='case/history.html'):
    """View test plan text history"""
    SUB_MODULE_NAME = 'cases'
    
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    if request.GET.get('from_plan'):
        from tcms.testplans.models import TestPlan
        tp = TestPlan.objects.get(plan_id = request.GET.get('from_plan'))
    else:
        tp = None
    
    tctxts = tc.text.all()
    return direct_to_template(request, template_name, {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'testcase': tc,
        'test_case_texts': tctxts,
        'select_case_text_version': int(request.REQUEST.get('case_text_version', 0)),
    })

@user_passes_test(lambda u: u.has_perm('testcases.add_testcase'))
def clone(request, template_name='case/clone.html'):
    """Clone one case or multiple case into other plan or plans"""
    from tcms.testplans.models import TestPlan
    from tcms.testplans.forms import SearchPlanForm
    from tcms.management.models import Product
    from forms import CloneCaseForm
    
    SUB_MODULE_NAME = 'cases'
    
    if not request.REQUEST.get('case'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one case is required.',
            next = 'javascript:window.history.go(-1)'
        ))
    
    # Do the clone action
    if request.method == 'POST':
        clone_form = CloneCaseForm(request.POST)
        clone_form.populate(case_ids = request.REQUEST.getlist('case'))
        
        if clone_form.is_valid():
            for tc_src in clone_form.cleaned_data['case']:
                if clone_form.cleaned_data['copy_case']:
                    tc_dest = TestCase.objects.create(
                        is_automated = tc_src.is_automated,
                        sortkey = tc_src.sortkey,
                        script = tc_src.script,
                        arguments = tc_src.arguments,
                        summary = tc_src.summary,
                        requirement = tc_src.requirement,
                        alias = tc_src.alias,
                        estimated_time = tc_src.estimated_time,
                        case_status = tc_src.case_status,
                        category = tc_src.category,
                        priority = tc_src.priority,
                        notes = tc_src.notes,
                        author = clone_form.cleaned_data['maintain_case_orignal_author'] and tc_src.author or request.user,
                        default_tester = clone_form.cleaned_data['maintain_case_orignal_default_tester'] and tc_src.author or request.user,
                    )
                    
                    tc_dest.add_text(
                        author = clone_form.cleaned_data['maintain_case_orignal_author'] and tc_src.author or request.user,
                        create_date = tc_src.latest_text().create_date,
                        action = tc_src.latest_text().action,
                        effect = tc_src.latest_text().effect,
                        setup = tc_src.latest_text().setup,
                        breakdown = tc_src.latest_text().breakdown
                    )
                    
                    for tag in tc_src.tag.all():
                        tc_dest.add_tag(tag = tag)
                else:
                    tc_dest = tc_src
                
                # Add the cases to plan
                for tp in clone_form.cleaned_data['plan']:
                    tp.add_case(case = tc_dest)
                    
                    # Clone the categories to new product
                    if clone_form.cleaned_data['copy_case']:
                        try:
                            tc_category = tp.product.category.get(
                                name = tc_src.category.name
                            )
                        except ObjectDoesNotExist, error:
                            tc_category = tp.product.category.create(
                                name = tc_src.category.name,
                                description = tc_src.category.description,
                            )
                        
                        tc_dest.category = tc_category
                        tc_dest.save()
                        del tc_category
                    
                    # Clone the components to new product
                    if clone_form.cleaned_data['copy_component'] and clone_form.cleaned_data['copy_case']:
                        for component in tc_src.component.all():
                            try:
                                new_c = tp.product.component.get(
                                    name = component.name
                                )
                            except ObjectDoesNotExist, error:
                                new_c = tp.product.component.create(
                                    name = component.name,
                                    initial_owner = request.user,
                                    description = component.description,
                                )
                            
                            try:
                                tc_dest.add_component(new_c)
                            except:
                                pass
            
            # Detect the number of items and redirect to correct one
            if len(clone_form.cleaned_data['case']) == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testcases.views.get', args=[tc_dest.case_id, ])
                )
            
            if len(clone_form.cleaned_data['plan']) == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get', args=[request.REQUEST.get('plan'), ])
                )
            
            # Otherwise it will prompt to user the clone action is successful.
            return HttpResponse(Prompt.render(
                request = request,
                info_type = Prompt.Info,
                info = 'Test case successful to clone, click following link to return to plans page.',
                next = reverse('tcms.testplans.views.all')
            ))
    
    # Generate search plan form
    if request.REQUEST.get('from_plan'):
        tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
        search_plan_form = SearchPlanForm(initial={ 'product': tp.product_id, 'is_active': True })
        search_plan_form.populate(product_id = tp.product_id)
    else:
        tp = None
        search_plan_form = SearchPlanForm()
    
    # Initial the clone case form
    clone_form = CloneCaseForm(initial={
        'case': request.REQUEST.getlist('case'),
        'copy_case': True,
        'maintain_case_orignal_author': True,
        'maintain_case_orignal_default_tester': True,
        'copy_component': True,
    })
    clone_form.populate(case_ids = request.REQUEST.getlist('case'))
    
    return direct_to_template(request, template_name, {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        # 'testcases': tcs,
        'search_form': search_plan_form,
        'clone_form': clone_form,
    })

@user_passes_test(lambda u: u.has_perm('testcases.add_testcaseattachment'))
def attachment(request, case_id, template_name='case/attachment.html'):
    """Manage test case attachments"""
    from tcms.testplans.models import TestPlan
    SUB_MODULE_NAME = 'cases'
    
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
        
    if request.REQUEST.get('from_plan'):
        try:
            tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
        except ObjectDoesNotExist, error:
            raise Http404(error)
    else:
        tp = None
        
    return direct_to_template(request, template_name, {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'testcase': tc,
    })

def get_log(request, case_id, template_name="management/get_log.html"):
    """Get the case log"""
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    return direct_to_template(request, template_name, {
        'object': tc
    })

@user_passes_test(lambda u: u.has_perm('testcases.change_testcasebug'))
def bug(request, case_id, template_name='case/get_bug.html'):
    """
    Process the bugs for cases
    """
    # FIXME: Rewrite these codes for Ajax.Request
    from forms import CaseBugForm
    
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    class CaseBugActions(object):
        __all__ = ['get_form', 'render', 'add', 'remove']
        
        def __init__(self, request, case, template_name):
            self.request = request
            self.case = case
            self.template_name = template_name
        
        def render_form(self):
            form = CaseBugForm(initial={
                'case': self.case,
            })
            if request.REQUEST.get('type') == 'table':
                return HttpResponse(form.as_table())
            
            return HttpResponse(form.as_p())
        
        def render(self, response = None):
            return direct_to_template(self.request, self.template_name, {
                'test_case': self.case,
                'response': response
            })
        
        def add(self):
            # FIXME: It's may use ModelForm.save() method here.
            #        Maybe in future.
            if not self.request.user.has_perm('testcases.add_testcasebug'):
                return self.render(response = 'Permission denied.')
            
            form = CaseBugForm(request.REQUEST)
            if not form.is_valid():
                return self.render(response = form.errors)
            
            try:
                self.case.add_bug(
                    bug_id = form.cleaned_data['bug_id'],
                    bug_system = form.cleaned_data['bug_system'],
                    summary = form.cleaned_data['summary'],
                    description = form.cleaned_data['description'],
                )
            except Warning, error:
                return self.render(response = error)
            
            return self.render()
        
        def remove(self):
            if not request.user.has_perm('testcases.delete_testcasebug'):
                return self.render(response = 'Permission denied.')
            
            try:
                self.case.remove_bug(request.REQUEST.get('id'))
            except ObjectDoesNotExist, error:
                return self.render(response = error)
            
            return self.render()
    
    case_bug_actions = CaseBugActions(
        request = request,
        case = tc,
        template_name = template_name
    )
    
    if not request.REQUEST.get('handle') in case_bug_actions.__all__:
        return case_bug_actions.render(response = 'Unrecognizable actions')
    
    func = getattr(case_bug_actions, request.REQUEST['handle'])
    return func()

@user_passes_test(lambda u: u.has_perm('testcases.change_testcaseplan'))
def plan(request, case_id):
    """
    Operating the case plan objects, such as add to remove plan from case
    
    Return: Hash
    """
    from django.utils import simplejson
    from tcms.testplans.models import TestPlan
    
    try:
        tc = TestCase.objects.get(case_id = case_id)
    except ObjectsDoesNotExist, error:
        raise Http404(error)
    
    if request.REQUEST.get('handle'):
        # Search the plans from database
        tps = TestPlan.objects.filter(
            plan_id__in = request.REQUEST.getlist('plan_id')
        )
        
        if not tps:
            return direct_to_template(request, 'case/get_plan.html', {
                'testplans': tps,
                'message': 'The plan id are not exist in database at all.'
            })
        
        # Add case plan action
        if request.REQUEST['handle'] == 'add':
            for tp in tps:
                tc.add_to_plan(tp)
        
        # Remove case plan action
        if request.REQUEST['handle'] == 'remove':
            for tp in tps:
                tc.remove_plan(tp)
    
    tps = tc.plan.all()
    tps = tps.select_related(
        'author__username', 'author__email', 'type__name', 'product__name'
    )
    
    return direct_to_template(request, 'case/get_plan.html', {
        'test_case': tc,
        'test_plans': tps,
    })
