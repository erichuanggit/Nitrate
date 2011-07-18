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

from models import TestCase, TestCaseStatus, TestCaseAttachment, TestCasePlan
from tcms.testplans.models import TestPlan
from itertools import groupby
from tcms.search.order import order_case_queryset
from tcms.search import remove_from_request_path

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
                    
                    return HttpResponseRedirect('%s#reviewcases' %
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
    
    from tcms.core.utils.raw_sql import RawSQL
    from tcms.testplans.models import TestPlan
    from tcms.management.models import Priority, TestTag
    
    # Intial the plan in plan details page
    if request.REQUEST.get('from_plan'):
        tp = TestPlan.objects.get(pk = request.REQUEST['from_plan'])
        SearchForm = CaseFilterForm
        # Hacking for case plan
        if request.REQUEST.get('template_type') == 'case':
            template_name = 'plan/get_cases.html'
        elif request.REQUEST.get('template_type') == 'review_case':
            template_name = 'plan/get_review_cases.html'
    else:
        tp = TestPlan.objects.none()
        SearchForm = SearchCaseForm
    # sorting
    order_by = request.REQUEST.get('order_by', 'create_date')
    asc = bool(request.REQUEST.get('asc', None))
    # Initial the form and template
    if request.REQUEST.get('a') in ('search', 'sort'):
        search_form = SearchForm(request.REQUEST)
    else:
        # Hacking for case plan
        confirmed_status_name = 'CONFIRMED'
        if request.REQUEST.get('template_type') == 'case': # 'c' is meaning component
            d_status = TestCaseStatus.objects.filter(name = confirmed_status_name)
        elif request.REQUEST.get('template_type') == 'review_case':
            d_status = TestCaseStatus.objects.exclude(name = confirmed_status_name)
        else:
            d_status = TestCaseStatus.objects.all()
        
        d_status_ids = d_status.values_list('pk', flat=True)
        
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
    tcs = order_case_queryset(tcs, order_by, asc)
    # Resort the order
    # if sorted by 'sortkey'(foreign key field)
    case_sort_by = request.REQUEST.get('case_sort_by')
    if case_sort_by:
        if case_sort_by not in  ['sortkey', '-sortkey']:
            tcs = tcs.order_by(case_sort_by)
        elif case_sort_by == 'sortkey':
            tcs = tcs.order_by('testcaseplan__sortkey')
        else:
            tcs = tcs.order_by('-testcaseplan__sortkey')
    
    # Initial the case ids
    if request.REQUEST.get('case'):
        selected_case_ids = map(lambda f: int(f), request.REQUEST.getlist('case'))
    else:
        selected_case_ids = tcs.values_list('pk', flat = True)
    
    # Get the tags own by the cases
    ttags = TestTag.objects.filter(testcase__in = tcs).distinct()
    # generating a query_url with order options
    query_url = remove_from_request_path(request, 'order_by')
    if asc:
        query_url = remove_from_request_path(request, 'asc')
    else:
        query_url = '%s&asc=True' % query_url
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'test_cases': tcs,
        'test_plan': tp,
        'search_form': search_form,
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
        'priorities': Priority.objects.all(),
        'case_own_tags': ttags,
        'query_url': query_url,
    })

def get(request, case_id, template_name = 'case/get.html'):
    """Get the case content"""
    from tcms.testruns.models import TestCaseRunStatus
    from tcms.core.utils.raw_sql import RawSQL
    from tcms.core.contrib.logs.models import TCMSLogModel
   # from tcms.core.models.base import TCMSBaseSharedModel

    # Get the case
    try:
        tc = TestCase.objects.select_related(
            'author', 'default_tester', 'category__name',
            'category__product__name', 'priority__name', 'case_status__name'
        ).get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    # Get the test plans
    tps = tc.plan.select_related('author', 'default_product', 'type').all()
    
    #log
    log_id = str(case_id)
    logs = TCMSLogModel.objects.filter(object_pk=log_id)

    logs = groupby(logs, lambda l: l.date)
    logs = [(day, list(actions)) for day, actions in logs]
    # Get the specific test plan
    if request.GET.get('from_plan'):
        try:
            tp = tps.get(pk = request.REQUEST['from_plan'])
        except TestPlan.DoesNotExist:
            raise Http404
    else:
        tp = None
    
    # Get the test case runs
    tcrs = tc.case_run.select_related(
        'run__summary', 'tested_by', 'assignee', 'case__category__name',
        'case__priority__name', 'case_run_status__name'
    ).all()
    
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    }).order_by('run__plan')
    runs_ordered_by_plan = groupby(tcrs, lambda t: t.run.plan)
    # FIXME: Just don't know why Django template does not evaluate a generator,
    # and had to evaluate the groupby generator manually like below.
    runs_ordered_by_plan = [(k, list(v)) for k, v in runs_ordered_by_plan]
    # Get the specific test case run
    if request.REQUEST.get('case_run_id'):
        tcr = tcrs.get(pk = request.REQUEST['case_run_id'])
    else:
        tcr = None
    
    # Get the case texts
    tc_text = tc.get_text_with_version(request.REQUEST.get('case_text_version'))
    
    # Switch the templates for different module
    template_types = {
        'case': 'case/get_details.html',
        'review_case': 'case/get_details_review.html',
        'case_run': 'case/get_details_case_run.html',
        'case_case_run': 'case/get_details_case_case_run.html',
        'execute_case_run': 'run/execute_case_run.html',
    }
    
    if request.REQUEST.get('template_type'):
        template_name = template_types.get(
            request.REQUEST['template_type'], 'case'
        )
    grouped_case_bugs = tcr and group_case_bugs(tcr.case.get_bugs())
    # Render the page
    return direct_to_template(request, template_name, {
        'logs': logs,
        'test_case': tc,
        'test_plan': tp,
        'test_plans': tps,
        'test_case_runs': tcrs,
        'runs_ordered_by_plan': runs_ordered_by_plan,
        'test_case_run': tcr,
        'grouped_case_bugs': grouped_case_bugs,
        'test_case_text': tc_text,
        'test_case_status': TestCaseStatus.objects.all(),
        'test_case_run_status': TestCaseRunStatus.objects.all(),
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
    })

def group_case_bugs(bugs):
    '''
    Group bugs using bug_id
    '''
    bugs = sorted(bugs, key=lambda b: b.bug_id)
    bugs = groupby(bugs, lambda b: b.bug_id)
    bugs = [(pk, list(_bugs)) for pk, _bugs in bugs]
    return bugs

def printable(request, template_name = 'case/printable.html'):
    """Create the printable copy for plan/case"""
    from tcms.testplans.models import TestPlan

    if not request.REQUEST.get('plan') and not request.REQUEST.get('case')\
    and not request.REQUEST.get('case_status'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one plan is required.',
        ))

    if request.REQUEST.get('plan'):
        tps = TestPlan.objects.filter(pk__in = request.REQUEST.getlist('plan'))
    else:
        tps = TestPlan.objects.none()
    
    if tps:
        for tp in tps:
            tp.case_list = tp.case.values_list('pk', flat=True)
    
    internal_query_maps = (
        # [Web request string, database queryset]
        ('plan', 'plan__pk__in'),
        ('case', 'pk__in'),
        ('case_status', 'case_status__pk__in')
    )
    
    query = {}
    for iqm in internal_query_maps:
        if request.REQUEST.get(iqm[0]):
            query[iqm[1]] = request.REQUEST.getlist(iqm[0])
    
    # Disabled cases ignored in default
    if not query.get('case_status__pk__in'):
        query['case_status__pk__in'] = TestCaseStatus.objects.exclude(
            name = 'DISABLED'
        ).values_list('pk', flat=True)
    
    tcs = TestCase.objects.filter(**query)
    return direct_to_template(request, template_name, {
        'test_plans': tps,
        'test_cases': tcs,
    })

def export(request, template_name = 'case/export.xml'):
    """Export the plan"""
    from datetime import datetime
    if not request.REQUEST.get('plan') and not request.REQUEST.get('case')\
    and not request.REQUEST.get('case_status'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one target is required.',
        ))
    timestamp = datetime.now()
    timestamp_str = '%02i-%02i-%02i' \
        % (timestamp.year, timestamp.month, timestamp.day)
    response = printable(request, template_name)
    response['Content-Disposition'] = 'attachment; filename=tcms-testcases-%s.xml' % timestamp_str
    return response

@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def edit(request, case_id, template_name = 'case/edit.html'):
    from forms import EditCaseForm, CaseNotifyForm
    from signals import EditCaseNotifyThread
    
    try:
        tc = TestCase.objects.select_related().get(case_id = case_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    if request.REQUEST.get('from_plan'):
        from tcms.testplans.models import TestPlan
        tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
    else:
        tp = None
    
    #CaseNotifyForm default to None
    n_form = None
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
            # Modify the contents
            fields = ['summary', 'case_status', 'category', 'priority',
                'notes', 'is_automated', 'is_automated_proposed', 'script',
                'arguments', 'requirement', 'alias'
            ]
            
            for field in fields:
                if getattr(tc, field) != form.cleaned_data[field]:
                    tc.log_action(request.user, 'Case %s changed from %s to %s in edit page.' % (
                        field, getattr(tc, field), form.cleaned_data[field]
                    ))
                    setattr(tc, field, form.cleaned_data[field])
            try:
                if tc.default_tester != form.cleaned_data['default_tester']:
                    tc.log_action(request.user, 'Case default tester changed from %s to %s in edit page.' % (
                        tc.default_tester_id and tc.default_tester, form.cleaned_data['default_tester']
                    ))
                    tc.default_tester = form.cleaned_data['default_tester']
            except ObjectDoesNotExist, error:
                pass
            
            # FIXME: Buggy here, timedelta from form cleaned data need to convert.
            #if tc.estimated_time != form.cleaned_data['estimated_time']:
            #    tc.log_action(request.user, 'Case estimated time changed from %s to %s in edit page.' % (
            #        tc.estimated_time, form.cleaned_data['estimated_time']
            #    ))
            tc.estimated_time = form.cleaned_data['estimated_time']
            tc.save()
            
            tc.add_text(
                author = request.user,
                action = form.cleaned_data['action'],
                effect = form.cleaned_data['effect'],
                setup = form.cleaned_data['setup'],
                breakdown = form.cleaned_data['breakdown']
            )
            
            # Clear and Add components into the case
            #tc.clear_components()
            #for component in form.cleaned_data['component']:
            #    tc.add_component(component = component)
            
            # Notification
            n_form = CaseNotifyForm(request.REQUEST)    # Notification form
            if n_form.is_valid():
                n_to = [request.user.email, tc.author.email]                # Initial Notification to
                
                if n_form.cleaned_data['default_tester_of_case'] and tc.default_tester_id:
                    n_to.append(tc.default_tester.email)
                
                if n_form.cleaned_data['authors_of_plans']:
                    n_to.extend(
                        tc.plan.values_list('author__email', flat=True)
                    )
                
                if n_form.cleaned_data['managers_of_runs']:
                    n_to.extend(
                        tc.case_run.values_list('run__manager__email', flat=True)
                    )
                
                if n_form.cleaned_data['default_testers_of_runs']:
                    n_to.extend(
                        tc.case_run.values_list('run__default_tester__email', flat=True)
                    )
                
                if n_form.cleaned_data['assignees_of_case_runs']:
                    n_to.extend(
                        tc.case_run.values_list('assignee__email', flat=True)
                    )
                
                if n_form.cleaned_data['specific_person']:
                    n_to.extend(n_form.cleaned_data['specific_person'])
                
                n_to = list(set(n_to))
                
                if not n_form.cleaned_data['editor']:
                    n_to.remove(request.user.email)
                
                # Sending the mail with threading
                EditCaseNotifyThread(
                    instance = tc,
                    cleaned_data = form.cleaned_data,
                    request = request,
                    to = n_to
                ).start()
            
            # Returns
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
        n_form = CaseNotifyForm(request.REQUEST)    # Notification form
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
        'notify_form': n_form,
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
    
    tp = None
    search_plan_form = SearchPlanForm()
    
    # Do the clone action
    if request.method == 'POST':
        clone_form = CloneCaseForm(request.POST)
        clone_form.populate(case_ids = request.REQUEST.getlist('case'))
        
        if clone_form.is_valid():
            for tc_src in clone_form.cleaned_data['case']:
                if clone_form.cleaned_data['copy_case']:
                    tc_dest = TestCase.objects.create(
                        is_automated = tc_src.is_automated,
                        is_automated_proposed = tc_src.is_automated_proposed,
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
                    for tp in clone_form.cleaned_data['plan']:
                        sortkey = tp.get_case_sortkey()
                        TestCasePlan.objects.create(plan = tp, case = tc_dest, sortkey = sortkey)
                    
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
                    
                    if clone_form.cleaned_data['copy_attachment']:
                        for attachment in tc_src.attachment.all():
                            TestCaseAttachment.objects.create(
                                case = tc_dest,
                                attachment = attachment,
                            )
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
            cases_count = len(clone_form.cleaned_data['case'])
            plans_count = len(clone_form.cleaned_data['plan'])
            
            if cases_count == 1 and plans_count == 1:
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('tcms.testcases.views.get', args=[tc_dest.pk, ]),
                    tp.pk
                ))
            
            if cases_count == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testcases.views.get', args=[tc_dest.pk, ])
                )
            
            if plans_count == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get', args=[tp.pk, ])
                )
            
            # Otherwise it will prompt to user the clone action is successful.
            return HttpResponse(Prompt.render(
                request = request,
                info_type = Prompt.Info,
                info = 'Test case successful to clone, click following link to return to plans page.',
                next = reverse('tcms.testplans.views.all')
            ))
    else:
        # Initial the clone case form
        clone_form = CloneCaseForm(initial={
            'case': request.REQUEST.getlist('case'),
            'copy_case': True,
            'maintain_case_orignal_author': True,
            'maintain_case_orignal_default_tester': True,
            'copy_component': True,
            'copy_attachment': True,
        })
        clone_form.populate(case_ids = request.REQUEST.getlist('case'))
    
    # Generate search plan form
    if request.REQUEST.get('from_plan'):
        tp = TestPlan.objects.get(plan_id = request.REQUEST['from_plan'])
        search_plan_form = SearchPlanForm(initial={ 'product': tp.product_id, 'is_active': True })
        search_plan_form.populate(product_id = tp.product_id)
    
    return direct_to_template(request, template_name, {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        # 'testcases': tcs,
        'search_form': search_plan_form,
        'clone_form': clone_form,
    })

@user_passes_test(lambda u: u.has_perm('testcases.add_testcasecomponent'))
def component(request):
    """
    Management test case components
    """
    # FIXME: It will update product/category/component at one time so far.
    # We may disconnect the component from case product in future.
    from tcms.core import forms
    from forms import CaseComponentForm
    
    class ComponentActions(object):
        """Component actions"""
        def __init__(self, request, tcs):
            self.ajax_response = {'rc': 0, 'response': 'ok', 'errors_list': []}
            self.request = request
            self.tcs = tcs
            self.product_id = request.REQUEST.get('product')
        
        def __get_form(self):
            self.form = CaseComponentForm(request.REQUEST)
            self.form.populate(product_id = self.product_id)
            return self.form
        
        def __check_form_validation(self):
            form = self.__get_form()
            if not form.is_valid():
                return 0, self.render_ajax(forms.errors_to_list(form))
            
            return 1, form
        
        def __check_perms(self, perm):
            if not self.request.user.has_perm('testcases.' + perm + '_testcasecomponent'):
                self.ajax_response['rc'] = 1
                self.ajax_response['response'] = 'Permission denied - ' + perm
                
                return 0, self.render_ajax(self.ajax_response)
                
            return 1, True
        
        def add(self):
            is_valid, perm = self.__check_perms('add')
            if not is_valid:
                return perm
            
            is_valid, form = self.__check_form_validation()
            if not is_valid:
                return form
            
            for tc in self.tcs:
                for c in form.cleaned_data['o_component']:
                    try:
                        tc.add_component(component = c)
                    except:
                        self.ajax_response['errors_list'].append({'case': tc.pk, 'component': c.pk})
            
            return self.render_ajax(self.ajax_response)
        
        def remove(self):
            is_valid, perm = self.__check_perms('delete')
            if not is_valid:
                return perm
            
            is_valid, form = self.__check_form_validation()
            if not is_valid:
                return form
            
            for tc in self.tcs:
                for c in form.cleaned_data['o_component']:
                    try:
                        tc.remove_component(component = c)
                    except:
                        self.ajax_response['errors_list'].append({'case': tc.pk, 'component': c.pk})
            
            return self.render_ajax(self.ajax_response)
        
        def update(self):
            is_valid, perm = self.__check_perms('change')
            if not is_valid:
                return perm
            
            is_valid, form = self.__check_form_validation()
            if not is_valid:
                return form
            
            #self.tcs.update(category = self.form.cleaned_data['category'])
            for tc in self.tcs:
                tc.clear_components()
                for c in form.cleaned_data['o_component']:
                    tc.add_component(component = c)
            
            return self.render_ajax(self.ajax_response)
        
        def render_ajax(self, response):
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def render_form(self):
            form = CaseComponentForm(initial={
                'product': self.product_id,
                #'category': self.request.REQUEST.get('category'),
                'component': self.request.REQUEST.getlist('o_component'),
            })
            form.populate(product_id = self.product_id)
            
            return HttpResponse(form.as_p())
    
    tcs = TestCase.objects.filter(pk__in = request.REQUEST.getlist('case'))
    if not tcs:
        raise Http404
    
    cas = ComponentActions(request = request, tcs = tcs)
    func = getattr(cas, request.REQUEST.get('a', 'render_form').lower())
    return func()

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
    
    if request.REQUEST.get('a'):
        # Search the plans from database
        if not request.REQUEST.getlist('plan_id'):
            return direct_to_template(request, 'case/get_plan.html', {
                'testplans': tps,
                'message': 'The case must specific one plan at leaset for some action',
            })
        
        tps = TestPlan.objects.filter(
            pk__in = request.REQUEST.getlist('plan_id')
        )
        
        if not tps:
            return direct_to_template(request, 'case/get_plan.html', {
                'testplans': tps,
                'message': 'The plan id are not exist in database at all.'
            })
        
        # Add case plan action
        if request.REQUEST['a'] == 'add':
            if not request.user.has_perm('testcases.add_testcaseplan'):
                return direct_to_template(request, 'case/get_plan.html', {
                    'test_case': tc,
                    'test_plans': tps,
                    'message': 'Permission denied',
                })
            
            for tp in tps:
                tc.add_to_plan(tp)
        
        # Remove case plan action
        if request.REQUEST['a'] == 'remove':
            if not request.user.has_perm('testcases.change_testcaseplan'):
                return direct_to_template(request, 'case/get_plan.html', {
                    'test_case': tc,
                    'test_plans': tps,
                    'message': 'Permission denied',
                })
            
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
