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

from datetime import datetime

from django.contrib.auth.decorators import user_passes_test
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from models import TestRun, TestCaseRun, TestCaseRunStatus, TCMSEnvRunValueMap

MODULE_NAME = "testruns"

@user_passes_test(lambda u: u.has_perm('testruns.add_testrun'))
def new(request, template_name = 'run/new.html'):
    """
    Display the create test run page
    """
    from tcms.testruns.forms import NewRunForm
    from tcms.testplans.models import TestPlan
    from tcms.testcases.models import TestCase
    from tcms.management.models import Version
    from tcms.core.utils.prompt import Prompt
    
    SUB_MODULE_NAME = "new_run"
    
    # If from_plan is not exist will redirect to plans for select a plan
    if not request.REQUEST.get('from_plan'):
        return HttpResponseRedirect(reverse('tcms.testplans.views.all'))
    
    plan_id = request.REQUEST['from_plan']
    
    # Case is required by a test run
    if not request.REQUEST.get('case'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one case is required by a run.',
            next = reverse('tcms.testplans.views.get', args=[plan_id, ]),
        ))
    
    # Ready to write cases to test plan
    tcs = TestCase.objects.filter(case_id__in = request.REQUEST.getlist('case'))
    tp = TestPlan.objects.select_related().get(plan_id = plan_id)
        
    num_unconfirmed_cases = 0
    for tc in tcs:
        # Hardcode here, the case_status_id is CONFIRMED
        if not tc.case_status.is_confirmed():
            num_unconfirmed_cases += 1
    
    if request.method == 'POST': # If the form has been submitted...
        form = NewRunForm(request.POST) # A form bound to the POST data
        if request.REQUEST.get('product'):
            form.populate(product_id = request.REQUEST['product'])
        else:
            form.populate(product_id = tp.product_id)
        
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            default_tester = form.cleaned_data['default_tester']
            
            tr = TestRun.objects.create(
                product_version = form.cleaned_data['product_version'],
                plan_text_version = tp.latest_text() and tp.latest_text().plan_text_version or 0,
                stop_date = None,
                summary = form.cleaned_data.get('summary'),
                notes = form.cleaned_data.get('notes'),
                plan = tp,
                build = form.cleaned_data['build'],
                manager = form.cleaned_data['manager'],
                default_tester = default_tester,
                estimated_time = form.cleaned_data['estimated_time'],
            )
            
            # Add case to the run
            loop = 1
            for case in form.cleaned_data['case']:
                tr.add_case_run(
                    case = case,
                    sortkey = loop * 10
                )
                loop += 1
            
            # Write the values into tcms_env_run_value_map table
            for key, value in request.REQUEST.items():
                if key.startswith('select_property_id_'):
                    try:
                        property_id = key.split('_')[3]
                        property_id = int(property_id)
                    except IndexError, error:
                        raise
                    except ValueError, error:
                        raise
                    
                    if request.REQUEST.get('select_property_value_%s' % property_id):
                        try:
                            value_id = int(request.REQUEST.get(
                                'select_property_value_%s' % property_id)
                            )
                        except ValueError, error:
                            raise
                        
                        TCMSEnvRunValueMap.objects.create(
                            run = tr,
                            value_id = request.REQUEST.get(
                                'select_property_value_%s' % property_id
                            ),
                        )
            
            return HttpResponseRedirect(
                reverse('tcms.testruns.views.get', args=[tr.run_id, ])
            )
    else:
        form = NewRunForm(initial={
            'summary': 'Test run for %s on %s' % (
                tp.name,
                tp.env_group.all() and tp.env_group.all()[0] or 'Unknown environment'
            ),
            'manager': tp.author.email,
            'default_tester': request.user.email,
            'product': tp.product_id,
            'product_version': tp.get_version_id(),
        })
        form.populate(product_id = tp.product_id)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'from_plan': plan_id,
        'test_plan': tp,
        'test_cases': tcs,
        'form': form,
        'num_unconfirmed_cases': num_unconfirmed_cases,
    })

@user_passes_test(lambda u: u.has_perm('testruns.delete_testrun'))
def delete(request, run_id):
    """
    Delete the test run
    - Maybe will be not use again
    """
    try:
        tr = TestRun.objects.select_related('manager', 'plan__author').get(
            run_id = run_id
        )
    except ObjectDoesNotExist, error:
        raise Http404
    
    if not tr.belong_to(request.user):
        return HttpResponse("<script>\
            alert('Permission denied - The run is not belong to you.');history.go(-1);\
            </script>"
        )
    
    if request.GET.get('sure', 'no') == 'no':
        return HttpResponse("<script>\n \
            if(confirm('Are you sure you want to delete this run %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) \
            { window.location.href='/run/%s/delete/?sure=yes' } \
            else { history.go(-1) };</script>" % ( run_id, run_id))
    elif request.GET.get('sure') == 'yes':
        try:
            plan_id = tr.plan_id
            tr.env_value.clear()
            tr.case_run.all().delete()
            tr.delete()
            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get', args=(plan_id, ))
            )
        except:
            return HttpResponse("<script>\
                alert('Delete failed');history.go(-1);\
                </script>"
            )
    else:
        return HttpResponse("<script>\
            alert('Nothing yet'); \
            history.go(-1); \
            </script>"
        )

def all(request, template_name = 'run/all.html'):
    """
    Read the test runs from database and display them
    """
    from tcms.testruns.forms import SearchRunForm
    from tcms.core.utils.raw_sql import RawSQL
    SUB_MODULE_NAME = "runs"
    
    if request.REQUEST.get('manager'):
        if request.user.is_authenticated() and (
            request.REQUEST.get('people') == request.user.username
            or request.REQUEST.get('people') == request.user.email
        ):
            SUB_MODULE_NAME = "my_runs"
    
    # Initial the values will be use if it's not a search
    query_result = False
    trs = None
    
    # If it's a search
    if request.REQUEST.items():
        search_form = SearchRunForm(request.REQUEST)
        
        if request.REQUEST.get('product'):
            search_form.populate(product_id = request.REQUEST['product'])
        else:
            search_form.populate()
        
        if search_form.is_valid():
            # It's a search here.
            query_result = True
            trs = TestRun.list(search_form.cleaned_data)
            trs = trs.select_related('manager', 'default_tester', 'build', 'plan', 'plan__product')
            
            # Further optimize by adding caserun attributes:
            trs = trs.extra(
                select={
                    'completed_case_run_percent': RawSQL.completed_case_run_percent,
                    'total_num_caseruns': RawSQL.total_num_caseruns,
                    'failed_case_run_percent': RawSQL.failed_case_run_percent,
                    'env_groups': RawSQL.environment_group_for_run,
                },
            )
    else:
        search_form = SearchRunForm()
        # search_form.populate()
    
    return direct_to_template(request, template_name, { 
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_runs': trs,
        'query_result': query_result,
        'search_form': search_form,
    })

def get(request, run_id, template_name = 'run/get.html'):
    from tcms.core.utils.raw_sql import RawSQL
    from tcms.core.utils.counter import CaseRunStatusCounter
    from tcms.testcases.models import TestCaseBug
    
    SUB_MODULE_NAME = "runs"
    
    # Get the test run
    try:
        tr = TestRun.objects.select_related().get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    # Get the test case runs belong to the run
    tcrs = tr.case_run.all()
    
    tcrs = tcrs.select_related(
        'case_run_status', 'build', 'environment',
        'environment__product', 'case__components', 'tested_by',
        'case__priority', 'case__category', 'case__author',
        'case', 'assignee'
    )
    
    # Get the bug count for each case run
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    })
    
    # Redirect to assign case page when a run does not contain any case run
    if not tcrs:
        return HttpResponseRedirect(
            reverse('tcms.testruns.views.assign_case', args=[run_id,])
        )
    
    # Count the status
    tcrs.count_by_status = CaseRunStatusCounter(tcrs)
    
    # Get the test case run bugs summary
    tcr_bugs = TestCaseBug.objects.select_related('bug_system').all()
    tcr_bugs = tcr_bugs.filter(case_run__case_run_id__in = tcrs.values_list('case_run_id', flat=True))
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'from_plan': request.GET.get('from_plan', False),
        'test_case_runs': tcrs,
        'test_case_run_bugs': tcr_bugs,
    })

def get_case_run(request, case_run_id, run_id = None, tr = None, response = None, template_name = 'run/execute_case_run.html'):
    """Return the page content of test case run in execute process"""
    if request.REQUEST.get('index_id'):
        forloop = {
            'counter': request.REQUEST['index_id']
        }
    else:
        return Http404('Index id is required')
    
    if not tr and not run_id:
        raise ValueError
    
    if run_id and not tr:
        tr = TestRun.objects.get(run_id = run_id)
    
    # Refresh the test case run object
    tcr = TestCaseRun.objects.select_related(
        'case', 'case__priority', 'case__author', 'tested_by', 'case__attachment'
        'assignee', 'build', 'case_run_status'
    )
    tcr = tcr.get(case_run_id = case_run_id)
    
    if request.REQUEST.get('type') == 'json':
        from django.core.serializers import serialize
        return HttpResponse(serialize('json', tcr))
    
    return direct_to_template(request, template_name, {
        'test_case_run': tcr,
        'testrun': tr,
        'case_run_status': TestCaseRunStatus.objects.all,
        'response': response,
        'forloop': forloop,
    })

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def edit(request, run_id, template_name = 'run/edit.html'):
    """
    Edit test plan view
    """
    from tcms.management.models import Version
    from tcms.testruns.forms import EditRunForm
    
    # Define the default sub module
    SUB_MODULE_NAME = 'runs'
    
    try:
        tr = TestRun.objects.select_related().get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    # If the form is submitted
    if request.method == "POST":
        form = EditRunForm(request.REQUEST)
        if request.REQUEST.get('product'):
            form.populate(product_id = request.REQUEST.get('product'))
        else:
            form.populate(product_id = tr.plan.product_id)
        
        #FIXME: Error handle
        if form.is_valid():
            tr.summary = form.cleaned_data['summary']
            # Permission hack
            if tr.manager == request.user or tr.plan.author == request.user:
                tr.manager = form.cleaned_data['manager']
            tr.default_tester = form.cleaned_data['default_tester']
            tr.build = form.cleaned_data['build']
            tr.product_version = form.cleaned_data['product_version']
            tr.notes = form.cleaned_data['notes']
            tr.stop_date = request.REQUEST.get('finished') and datetime.now() or None
            tr.estimated_time = form.cleaned_data['estimated_time']
            tr.save()
            return HttpResponseRedirect(
                reverse('tcms.testruns.views.get', args=[run_id, ])
            )
    else:
        # Generate a blank form
        form = EditRunForm(initial={
            'summary': tr.summary,
            'manager': tr.manager.email,
            'default_tester': tr.default_tester and tr.default_tester.email or None,
            'product': tr.build.product_id,
            'product_version': tr.get_version_id(),
            'build': tr.build_id,
            'notes': tr.notes,
            'finished': tr.stop_date,
            'estimated_time': tr.estimated_time,
        })
        form.populate(product_id = tr.build.product_id)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'form': form,
    })

@user_passes_test(lambda u: u.has_perm('testruns.change_testcaserun'))
def execute(request, run_id, template_name = 'run/execute.html'):
    SUB_MODULE_NAME = "runs"
    
    tr = TestRun.objects.select_related().get(run_id = run_id)
    
    # Get the test cases belong to the run
    testrun_relate_testcases = tr.case_run.all()
    if request.REQUEST.get('case_run_status_id'):
        testrun_relate_testcases = testrun_relate_testcases.filter(
            case_run_status__id = request.REQUEST.get('case_run_status_id')
        )
    
    if request.REQUEST.get('case_run_status'):
        testrun_relate_testcases = testrun_relate_testcases.filter(
            case_run_status__name = request.REQUEST.get('case_run_status').upper()
        )
    
    testrun_relate_testcases = testrun_relate_testcases.select_related(
        'case_run_status', 'build',
        'case__components', 'tested_by',
        'case__priority', 'case__category', 'case__author',
        'case', 'assignee'
    )
    
    for tcr in testrun_relate_testcases:
        if not tcr.running_date:
            tcr.running_date = datetime.now()
            tcr.save()
    
    # Query all of case run status
    case_run_status = TestCaseRunStatus.objects.all()
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testrun': tr,
        'testrun_relate_testcases': testrun_relate_testcases,
        'case_run_status': case_run_status,
    })

@user_passes_test(lambda u: u.has_perm('testruns.change_testcaserun'))
def change_case_run_status(request, run_id, case_run_id, template_name='run/execute_case_run.html'):
    from urllib import unquote
    
    ajax_response = { 'response': 'ok' }
    
    try:
        # Get the test run
        tr = TestRun.objects.get(run_id = run_id)
        
        # Get the test case run
        tcr = TestCaseRun.objects.get(case_run_id = case_run_id)
        
        # Get the test case run status
        tcr_status = TestCaseRunStatus.objects.get(id = request.REQUEST.get('case_run_status_id'))
    except ObjectDoesNotExist, error:
        ajax_response['response'] = error
        
        return get_case_run(
            request = request,
            case_run_id = tcr.case_run_id,
            tr = tr,
            response = ajax_response['response']
        )
    
    # Check the confict case run status id
    if str(tcr.case_run_status_id) != request.REQUEST.get(
        'orig_case_run_status_id', str(tcr.case_run_status_id)
    ):
        ajax_response['response'] = 'Someone has done changes in the time you had this page open, The changes is refreshed in the page, please decide how the case run status.'
        
        return get_case_run(
            request = request,
            case_run_id = tcr.case_run_id,
            tr = tr,
            response = ajax_response['response']
        )
    
    # Change the status change history
    if tcr.case_run_status != tcr_status:
        tcr.log_action(request.user, 'Status changed from %s to %s' % (
            tcr.case_run_status.name,
            tcr_status.name,
        ))
    
    if not tcr.assignee_id or tcr.assignee != request.user:
        tcr.log_action(request.user, 'Assignee changed from %s to %s by %s' % (
            tcr.assignee_id and tcr.assignee,
            request.user.email,
            request.user.email,
        ))
    
    # Change the information
    tcr.tested_by = request.user
    tcr.assignee = request.user
    tcr.case_run_status_id = tcr_status.id
    tcr.close_date = datetime.now()
    
    tcr.save()
    # Did we just finish the last caserun in an unfinished run?
    # If so, the run is now finished : (ticket #355):
    if tr.stop_date is None:
        if tr.check_all_case_runs(case_run_id = tcr.case_run_id):
            tr.stop_date = datetime.now()
            tr.save()
    
    return get_case_run(request, case_run_id = tcr.case_run_id, tr = tr)

def report(request, run_id, template_name = 'run/report.html'):
    return get(request, run_id, template_name)

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def suggest_summary(request):
    '''
       Generate a suggested summary for a new run, as per:
       [ NewRun_Name_autofill: the new run page shall contain a field for
        entering the name of the new plan. If the user has not touched the
        field, the field shall automatically populate with text of the form:
          * (planname):(environmentname):(number of runs made with this plan/environment combo) 

        and the field shall update as environments are selected, until the
        user manually edits the field. For example, a sample value might read:
          "OpenGL Performance:x86_64:001"          
    '''
    from django.utils.simplejson import dumps as json_dumps
    from tcms.testplans.models import TestPlan
    from tcms.management.models import TestEnvironment
    
    plan_id = request.GET['plan_id']
    build_id = request.GET['build_id']
    env_id = request.GET['env_id']
    product_id = request.GET['product_id']
    
    numRuns = TestRun.objects.filter(
        plan__plan_id=plan_id,
        environment__environment_id=env_id
    ).count()
    plan = TestPlan.objects.get(plan_id=plan_id)
    env = TestEnvironment.objects.get(environment_id=env_id)
    summary = '%s:%s:%03i' % \
              (plan.name, env.name, numRuns+1)
    response = {'suggestedSummary': summary}
    return HttpResponse(json_dumps(response))

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def bug(request, run_id, case_run_id, template_name = 'run/execute_case_run.html'):
    """
    Process the bugs for case runs
    """
    # FIXME: Rewrite these codes for Ajax.Request
    #        And write a render method to get the page.
    from tcms.testcases.forms import CaseBugForm
    
    class CaseRunBugActions(object):
        __all__ = ['add', 'file', 'remove', 'render', 'render_form']
        
        def __init__(self, request, case_run, template_name):
            self.request = request
            self.case_run = case_run
            self.template_name = template_name
       
        def add(self):
            if not self.request.user.has_perm('testcases.add_testcasebug'):
                return self.render(response = 'Permission denied')
            
            form = CaseBugForm(request.REQUEST)
            if not form.is_valid():
                return self.render(response = form.errors)
            
            tcr.add_bug(
                bug_id = form.cleaned_data['bug_id'],
                bug_system = form.cleaned_data['bug_system'],
                summary = form.cleaned_data['summary'],
                description = form.cleaned_data['description'],
            )
            tcr.set_current()
            
            return self.render()
        
        def file(self):
            from django.conf import settings
            from tcms.core.utils.bugtrackers import Bugzilla
            
            rh_bz = Bugzilla(settings.BUGZILLA_URL)
            url = rh_bz.make_url(self.case_run.run, self.case_run, self.case_run.case_text_version)
            
            return HttpResponseRedirect(url)
        
        def remove(self):
            if not self.request.user.has_perm('testcases.delete_testcasebug'):
                return self.render(response = 'Permission denied')
            
            try:
                self.case_run.remove_bug(self.request.REQUEST.get('id'))
            except ObjectDoesNotExist, error:
                return self.render(response = error)
            
            self.case_run.set_current()
            
            return self.render()
        
        def render(self, response = None):
            return get_case_run(
                request = self.request,
                case_run_id = self.case_run.case_run_id,
                run_id = self.case_run.run_id,
                response = response,
            )
        
        def render_form(self):
            form = CaseBugForm(initial={
                'case_run': self.case_run.case_run_id,
                'case': self.case_run.case_id,
            })
            if self.request.REQUEST.get('type') == 'table':
                return HttpResponse(form.as_table())
            
            return HttpResponse(form.as_p())
    
    try:
        tcr = TestCaseRun.objects.get(case_run_id = case_run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    crba = CaseRunBugActions(
        request = request,
        case_run = tcr,
        template_name = template_name
    )
    
    if not request.REQUEST.get('handle') in crba.__all__:
        return crba.render(response = 'Unrecognizable actions')
    
    func = getattr(crba, request.REQUEST['handle'])
    return func()

def clone(request, run_id, template_name='run/clone.html'):
    """Clone test run to another build"""
    from tcms.testruns.forms import RunCloneForm
    
    SUB_MODULE_NAME = "runs"
    
    try:
        tr = TestRun.objects.select_related().get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    clone_form = RunCloneForm(initial={
        'summary': tr.summary,
        'notes': tr.notes,
        'manager': tr.manager.email,
        'product': tr.plan.product_id,
        'version': tr.plan.get_version_id,
        'build': tr.build_id,
        'default_tester': tr.default_tester_id and tr.default_tester.email or '',
        'use_newest_case_text': True,
    })
    clone_form.populate(product_id = tr.plan.product_id)
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'clone_form': clone_form,
        'test_run': tr,
    })

def order_case(request, run_id):
    """
    Resort case with new order
    """
    # Current we should rewrite all of cases belong to the plan.
    # Because the cases sortkey in database is chaos,
    # Most of them are None.
    from tcms.core.utils.prompt import Prompt
    
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    if not request.REQUEST.get('case_run'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one case is required by re-oder in run.',
            next = reverse('tcms.testruns.views.get', args=[run_id, ]),
        ))
    
    case_run_ids = request.REQUEST.getlist('case_run')
    tcrs = TestCaseRun.objects.filter(case_run_id__in = case_run_ids)
    
    for tcr in tcrs:
        new_sort_key = (case_run_ids.index(str(tcr.case_run_id)) + 1) * 10
        if tcr.sortkey != new_sort_key:
            tcr.sortkey = new_sort_key
            tcr.save()
    
    return HttpResponseRedirect(
        reverse('tcms.testruns.views.get', args=[run_id, ])
    )

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def change_status(request, run_id):
    """Change test run finished or running"""
    from datetime import datetime
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    if request.GET.get('finished') == '1':
        tr.stop_date = datetime.now()
    else:
        tr.stop_date = None
    
    tr.save()
    
    return HttpResponseRedirect(
        reverse('tcms.testruns.views.get', args=[run_id, ])
    )

@user_passes_test(lambda u: u.has_perm('testruns.delete_testcaserun'))
def remove_case_run(request, run_id):
    """Remove specific case run from the run"""
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    case_runs = tr.case_run.filter(case_run_id__in = request.REQUEST.getlist('case_run'))
    
    case_runs.delete()
    
    return HttpResponseRedirect(reverse('tcms.testruns.views.get', args=[run_id]))

@user_passes_test(lambda u: u.has_perm('testruns.add_testcaserun'))
def assign_case(request, run_id, template_name="run/assign_case.html"):
    """
    Assign case to run
    """
    SUB_MODULE_NAME = "runs"
    
    try:
        tr = TestRun.objects.select_related('plan', 'manager__email', 'build')
        tr = tr.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    tcs = tr.plan.case.select_related('author__email', 'category', 'priority')
    ctcs = tcs.filter(case_status__name ='CONFIRMED')
    
    tcrs = tr.case_run.all()
    etcrs_id = tcrs.values_list('case', flat=True) #Exist case ids
    
    if request.method == 'POST':
        ncs_id = request.REQUEST.getlist('case') # New case ids
        
        for nc_id in ncs_id:
            if nc_id in etcrs_id:
                ncs_id.remove(nc_id)
                
        ncs = tcs.filter(case_id__in = ncs_id)
        
        if request.REQUEST.get('_use_plan_sortkey'):
            for nc in ncs:
                tr.add_case_run(
                    case = nc,
                    sortkey = nc.sortkey,
                )
        else:
            for nc in ncs:
                tr.add_case_run(
                    case = nc,
                )
                
        return HttpResponseRedirect(reverse('tcms.testruns.views.get', args=[tr.run_id, ]))
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'confirmed_cases': ctcs,
        'test_case_run': tcrs,
        'exist_case_run_ids': etcrs_id,
    })

def cc(request, run_id):
    """
    Operating the test run cc objects, such as add to remove cc from run
    
    Return: Hash
    """
    from django.db.models import Q
    from django.contrib.auth.models import User
    
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    if request.REQUEST.get('do'):
        if not request.REQUEST.get('user'):
            return direct_to_template(request, 'run/get_cc.html', {
                'test_run': tr,
                'message': 'User name or email is required by this operation'
            })
        
        try:
            user = User.objects.get(
                Q(username = request.REQUEST['user'])
                | Q(email = request.REQUEST['user'])
            )
        except ObjectDoesNotExist, error:
            return direct_to_template(request, 'run/get_cc.html', {
                'test_run': tr,
                'message': 'The user you typed is not exist in database'
            })        
        if request.REQUEST['do'] == 'add':
            tr.add_cc(user = user)
        
        if request.REQUEST['do'] == 'remove':
            tr.remove_cc(user = user)
    
    return direct_to_template(request, 'run/get_cc.html', {
        'test_run': tr,
    })

def update(request, run_id):
    """
    Update the IDLE cases to newest text
    """
    from tcms.core.utils import Prompt
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    tcrs = tr.case_run.filter(case_run_status__name = 'IDLE')
    count = 0
    updated_tcrs = ''
    for tcr in tcrs:
        lctv = tcr.latest_text().case_text_version
        if tcr.case_text_version != lctv:
            count += 1
            updated_tcrs += '<li>%s: %s -> %s</li>' % (
                tcr.case.summary, tcr.case_text_version, lctv
            )
            tcr.case_text_version = lctv
            tcr.save()
    
    info = '<p>%s case run(s) succeed to update, following is the list:</p>\
    <ul>%s</ul>' % (count, updated_tcrs)
    
    del tr, tcrs, count, updated_tcrs
    
    return HttpResponse(Prompt.render(
        request = request,
        info_type = Prompt.Info,
        info = info,
        next = reverse('tcms.testruns.views.get', args=[run_id,]),
    ))

def env_value(request):
    """Run environment property edit function"""
    from django.utils import simplejson
    from tcms.management.models import TCMSEnvValue
    
    trs = TestRun.objects.filter(run_id__in = request.REQUEST.getlist('run_id'))
    
    class RunEnvActions(object):
        def __init__(self, requet, trs):
            self.__all__ = ['add', 'remove', 'change']
            self.ajax_response = {'rc': 0, 'response': 'ok'}
            self.request = request
            self.trs = trs
        
        def has_no_perm(self, perm):
            if self.request.user.has_perm(perm + '_tcmsenvrunvaluemap'):
                return False
            
            return {'rc': 1, 'response': 'Permission deined - %s' % perm}
        
        def get_env_value(self, env_value_id):
            return TCMSEnvValue.objects.get(id = env_value_id)
        
        def add(self):
            chk_perm = self.has_no_perm('add')
            
            if chk_perm:
                return HttpResponse(simplejson.dumps(chk_perm))
            
            try:
                for tr in self.trs:
                    o, c = tr.add_env_value(env_value = self.get_env_value(
                        request.REQUEST.get('env_value_id')
                    ))
                    
                    if not c:
                        self.ajax_response = {
                            'rc': 1, 'response': 'The value is exist for this run'
                        }
            except ObjectDoesNotExist, errors:
                self.ajax_response = {'rc': 1, 'response': errors}
            except:
                raise
            
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def add_mulitple(self):
            chk_perm = self.has_no_perm('add')
            if chk_perm:
                return HttpResponse(simplejson.dumps(chk_perm))
            
            # Write the values into tcms_env_run_value_map table
            for key, value in self.request.REQUEST.items():
                if key.startswith('select_property_id_'):
                    try:
                        property_id = key.split('_')[3]
                        property_id = int(property_id)
                    except IndexError, error:
                        raise
                    except ValueError, error:
                        raise
                    
                    if request.REQUEST.get('select_property_value_%s' % property_id):
                        try:
                            value_id = int(request.REQUEST.get(
                                'select_property_value_%s' % property_id)
                            )
                        except ValueError, error:
                            raise
                        
                        for tr in self.trs:
                            TCMSEnvRunValueMap.objects.create(
                                run = tr,
                                value_id = request.REQUEST.get(
                                    'select_property_value_%s' % property_id
                                ),
                            )
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def remove(self):
            chk_perm = self.has_no_perm('delete')
            if chk_perm:
                return HttpResponse(simplejson.dumps(chk_perm))
            
            try:
                for tr in self.trs:
                    tr.remove_env_value(env_value = self.get_env_value(
                        request.REQUEST.get('env_value_id')
                    ))
            except:
                pass
            
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def change(self):
            chk_perm = self.has_no_perm('change')
            if chk_perm:
                return HttpResponse(simplejson.dumps(chk_perm))
            
            try:
                for tr in self.trs:
                    tr.remove_env_value(env_value = self.get_env_value(
                        request.REQUEST.get('old_env_value_id')
                    ))
                    
                    tr.add_env_value(env_value = self.get_env_value(
                        request.REQUEST.get('new_env_value_id')
                    ))
            except:
                raise
            
            return HttpResponse(simplejson.dumps(self.ajax_response))
    
    run_env_actions = RunEnvActions(request, trs)
    
    if not request.REQUEST.get('handle') in run_env_actions.__all__:
        ajax_response = {'rc': 1, 'response': 'Unrecognizable actions'}
        return HttpResponse(simplejson.dumps(ajax_response))
    
    func = getattr(run_env_actions, request.REQUEST['handle'])
    
    try:
        return func()
    except:
        raise
