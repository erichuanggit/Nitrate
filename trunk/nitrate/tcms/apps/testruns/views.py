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

from tcms.core.utils.prompt import Prompt
from models import TestRun, TestCaseRun, TestCaseRunStatus, TCMSEnvRunValueMap
from tcms.search.order import order_run_queryset
from tcms.search import remove_from_request_path

from tcms.settings import ERRATA_URL_PREFIX

MODULE_NAME = "testruns"

@user_passes_test(lambda u: u.has_perm('testruns.add_testrun'))
def new(request, template_name = 'run/new.html'):
    """
    Display the create test run page
    """
    from tcms.apps.testruns.forms import NewRunForm
    from tcms.apps.testruns.models import TestCaseRun
    from tcms.apps.testplans.models import TestPlan
    from tcms.apps.testcases.models import TestCase
    from tcms.management.models import Version
    from tcms.core.utils.prompt import Prompt
    from tcms.apps.testcases.models import TestCasePlan


    SUB_MODULE_NAME = "new_run"

    # If from_plan does not exist will redirect to plans for select a plan
    if not request.REQUEST.get('from_plan'):
        return HttpResponseRedirect(reverse('tcms.apps.testplans.views.all'))

    plan_id = request.REQUEST['from_plan']

    # Case is required by a test run
    if not request.REQUEST.get('case'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one case is required by a run.',
            next = reverse('tcms.apps.testplans.views.get', args=[plan_id, ]),
        ))

    # Ready to write cases to test plan
    tcs = TestCase.objects.filter(case_id__in = request.REQUEST.getlist('case'))
    tp = TestPlan.objects.select_related().get(plan_id = plan_id)
    tcrs = TestCaseRun.objects.filter(case_run_id__in = request.REQUEST.getlist('case_run_id'))

    num_unconfirmed_cases = 0
    for tc in tcs:
        # Hardcode here, the case_status_id is CONFIRMED
        if not tc.case_status.is_confirmed():
            num_unconfirmed_cases += 1

    if request.REQUEST.get('POSTING_TO_CREATE'): # Dirty work around here by using argument determination
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
                errata_id = form.cleaned_data['errata_id'],
            )

            keep_status = form.cleaned_data['keep_status']
            keep_assign= form.cleaned_data['keep_assignee']

            loop = 1

            # not reserve assignee and status
            if not keep_assign and not keep_status:
                for case in form.cleaned_data['case']:
                    try:
                        tcp = TestCasePlan.objects.get(plan=tp, case=case)
                        sortkey = tcp.sortkey
                    except ObjectDoesNotExist, error:
                        sortkey = loop * 10
                    tr.add_case_run(
                        case = case,
                        sortkey = sortkey,
                    )
                    loop += 1

            # Add case to the run
            for tcr in tcrs:
                if (keep_status and keep_assign):
                    tr.add_case_run(
                        case = tcr.case,
                        assignee = tcr.assignee,
                        case_run_status = tcr.case_run_status,
                        sortkey = tcr.sortkey or loop * 10
                    )
                    loop += 1
                elif keep_status and not keep_assign:
                    tr.add_case_run(
                        case = tcr.case,
                        case_run_status = tcr.case_run_status,
                        sortkey = tcr.sortkey or loop * 10
                    )
                    loop += 1
                elif keep_assign and not keep_status:
                    tr.add_case_run(
                        case = tcr.case,
                        assignee = tcr.assignee,
                        sortkey = tcr.sortkey or loop * 10
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
                reverse('tcms.apps.testruns.views.get', args=[tr.run_id, ])
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
                reverse('tcms.apps.testplans.views.get', args=(plan_id, ))
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
    from tcms.apps.testruns.forms import SearchRunForm
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
    order_by = request.REQUEST.get('order_by', 'create_date')
    asc = bool(request.REQUEST.get('asc', None))
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
            trs = trs.select_related(
                'manager', 'default_tester', 'build', 'plan', 'build__product__name',
            )

            # Further optimize by adding caserun attributes:
            trs = trs.extra(
                select={
                    'env_groups': RawSQL.environment_group_for_run,
                },
            )
            trs = order_run_queryset(trs, order_by, asc)
    else:
        search_form = SearchRunForm()
        # search_form.populate()
    # generating a query_url with order options
    query_url = remove_from_request_path(request, 'order_by')
    if asc:
        query_url = remove_from_request_path(request, 'asc')
    else:
        query_url = '%s&asc=True' % query_url
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_runs': trs,
        'query_result': query_result,
        'search_form': search_form,
        'query_url': query_url,
    })

def get(request, run_id, template_name = 'run/get.html'):
    from tcms.core.utils import clean_request
    from tcms.core.utils.raw_sql import RawSQL
    from tcms.core.utils.counter import CaseRunStatusCounter
    from tcms.apps.testcases.models import TestCaseBug
    from tcms.apps.management.models import Priority
    SUB_MODULE_NAME = "runs"

    # Get the test run
    try:
        tr = TestRun.objects.select_related().get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404

    # Get the test case runs belong to the run
    tcrs = tr.case_run.all()

    # Count the status
    status_counter = CaseRunStatusCounter(tcrs)

    # Redirect to assign case page when a run does not contain any case run
    if not tcrs.count():
        return HttpResponseRedirect(
            reverse('tcms.apps.testruns.views.assign_case', args=[run_id,])
        )

    # Continue to search the case runs with conditions
    tcrs = tcrs.filter(**clean_request(request))
    if request.REQUEST.get('order_by'):
        tcrs = tcrs.order_by(request.REQUEST['order_by'])

    tcrs = tcrs.select_related(
        'run', 'case_run_status', 'build', 'environment',
        'environment__product', 'case__components', 'tested_by',
        'case__priority', 'case__category', 'case__author',
        'case', 'assignee'
    )

    # Get the bug count for each case run
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    })
    tcrs = tcrs.distinct()
    # Get the test case run bugs summary
    tcr_bugs = TestCaseBug.objects.select_related('bug_system').all()
    tcr_bugs = tcr_bugs.filter(case_run__case_run_id__in = tcrs.values_list('case_run_id', flat=True))
    tcr_bugs = tcr_bugs.values_list('bug_id', flat=True)
    tcr_bugs = set(tcr_bugs)
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'from_plan': request.GET.get('from_plan', False),
        'test_case_runs': tcrs,
        'status_counter': status_counter,
        'test_case_run_bugs': tcr_bugs,
        'test_case_run_status': TestCaseRunStatus.objects.order_by('pk'),
        'priorities': Priority.objects.all(),
        'errata_url_prefix': ERRATA_URL_PREFIX,
    })

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def edit(request, run_id, template_name = 'run/edit.html'):
    """
    Edit test plan view
    """
    from tcms.management.models import Version
    from tcms.apps.testruns.forms import EditRunForm

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

        #FIXME: Error handler
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
            tr.errata_id = form.cleaned_data['errata_id']
            tr.save()
            return HttpResponseRedirect(
                reverse('tcms.apps.testruns.views.get', args=[run_id, ])
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
            'errata_id': tr.errata_id,
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
    """Execute test run"""
    return get(request, run_id, template_name)

def report(request, run_id, template_name = 'run/report.html'):
    return get(request, run_id, template_name)

@user_passes_test(lambda u: u.has_perm('testruns.change_testcaserun'))
def set_current(request, case_run_id):
    """Set the case to be current"""
    from django.utils import simplejson
    try:
        TestCaseRun.objects.get(pk = case_run_id).set_current()
    except:
        pass

    return HttpResponse(simplejson.dumps({'rc': 0, 'response': 'ok'}))

@user_passes_test(lambda u: u.has_perm('testruns.change_testrun'))
def bug(request, case_run_id, template_name = 'run/execute_case_run.html'):
    """
    Process the bugs for case runs
    """
    from django.utils import simplejson
    from tcms.apps.testcases.forms import CaseBugForm

    class CaseRunBugActions(object):
        __all__ = ['add', 'file', 'remove', 'render_form']

        def __init__(self, request, case_run, template_name):
            self.request = request
            self.case_run = case_run
            self.template_name = template_name
            self.default_ajax_response = {'rc': 0, 'response': 'ok'}

        def add(self):
            if not self.request.user.has_perm('testcases.add_testcasebug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.ajax_response(response = response)

            form = CaseBugForm(request.REQUEST)
            if not form.is_valid():
                response = {'rc': 1, 'response': form.errors}
                return self.ajax_response(response = response)

            tcr.add_bug(
                bug_id = form.cleaned_data['bug_id'],
                bug_system = form.cleaned_data['bug_system'],
                summary = form.cleaned_data['summary'],
                description = form.cleaned_data['description'],
            )
            # tcr.set_current()

            return self.ajax_response()

        def ajax_response(self, response = None):
            if not response:
                response = self.default_ajax_response

            return HttpResponse(simplejson.dumps(response))

        def file(self):
            from django.conf import settings
            from tcms.core.utils.bugtrackers import Bugzilla

            rh_bz = Bugzilla(settings.BUGZILLA_URL)
            url = rh_bz.make_url(self.case_run.run, self.case_run, self.case_run.case_text_version)

            return HttpResponseRedirect(url)

        def remove(self):
            if not self.request.user.has_perm('testcases.delete_testcasebug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.render(response = response)

            try:
                bug_id = self.request.REQUEST.get('bug_id')
                run_id = self.request.REQUEST.get('case_run')
                self.case_run.remove_bug(bug_id, run_id)
            except ObjectDoesNotExist, error:
                response = {'rc': 1, 'response': str(error)}
                return self.ajax_response(response=response)

            # self.case_run.set_current()

            return self.ajax_response()

        #def render(self, response = None):
        #    return get_case_run(
        #        request = self.request,
        #        case_run_id = self.case_run.case_run_id,
        #        run_id = self.case_run.run_id,
        #        response = response,
        #    )

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

    if not request.REQUEST.get('a') in crba.__all__:
        return crba.ajax_response(response = {'rc': 1, 'response': 'Unrecognizable actions'})

    func = getattr(crba, request.REQUEST['a'])
    return func()

def clone_with_filteredCaseRun(request,run_id,template_name='run/clone.html'):
    import urllib
    from tcms.apps.testruns.forms import RunCloneForm

    SUB_MODULE_NAME = "runs"
    try:
        tr=TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    if request.REQUEST.get('case_run'):
        tcrs=tr.case_run.filter(pk__in = request.REQUEST.getlist('case_run'))
    else:
        tcrs=[]

    if not tcrs:
        return HttpResponse(Prompt.render(
                    request=request,
                    info_type=Prompt.Info,
                    info='At least one case is required by a run',
                    next = request.META.get('HTTP_REFERER', '/')))

    if not request.REQUEST.get('submit'):
        form=RunCloneForm(initial={
            'summary':tr.summary,
            'notes':tr.notes,
            'manager':tr.manager.email,
            'product':tr.plan.product_id,
            'product_version':tr.get_version_id(),
            'build':tr.build_id,
            'default_tester':tr.default_tester_id and tr.default_tester.email or '',
            'use_newest_case_text':True,
        })

        form.populate(product_id=tr.plan.product_id)

        return direct_to_template(request,template_name,{
            'module':MODULE_NAME,
            'sub_module':SUB_MODULE_NAME,
            'clone_form':form,
            'test_run':tr,
            'cases_run':tcrs,
        })


def clone(request, template_name='run/clone.html'):
    """Clone test run to another build"""
    import urllib
    from tcms.apps.testruns.forms import RunCloneForm, MulitpleRunsCloneForm

    SUB_MODULE_NAME = "runs"

    trs = TestRun.objects.select_related()
    trs = trs.filter(pk__in = request.REQUEST.getlist('run'))

    if not trs:
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one run is required',
            next = request.META.get('HTTP_REFERER', '/')
        ))

    # Generate the clone run page for one run
    if len(trs) == 1 and not request.REQUEST.get('submit'):
        tr = trs[0]
        tcrs = tr.case_run.all()
        form = RunCloneForm(initial={
            'summary': tr.summary,
            'notes': tr.notes,
            'manager': tr.manager.email,
            'product': tr.plan.product_id,
            'product_version': tr.get_version_id(),
            'build': tr.build_id,
            'default_tester': tr.default_tester_id and tr.default_tester.email or '',
            'use_newest_case_text': True,
            'errata_id': tr.errata_id,
        })
        form.populate(product_id = tr.plan.product_id)

        return direct_to_template(request, template_name, {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'clone_form': form,
            'test_run': tr,
            'cases_run': tcrs,
        })

    # Process multiple runs clone page
    template_name = 'run/clone_multiple.html'

    if request.method == "POST":
        form = MulitpleRunsCloneForm(request.REQUEST)
        form.populate(trs = trs, product_id = request.REQUEST.get('product'))
        if form.is_valid():
            for tr in trs:
                n_tr = TestRun.objects.create(
                    product_version = form.cleaned_data['product_version'],
                    plan_text_version = tr.plan_text_version,
                    summary = tr.summary,
                    notes = tr.notes,
                    estimated_time = tr.estimated_time,
                    plan = tr.plan,
                    build = form.cleaned_data['build'],
                    manager = form.cleaned_data['update_manager'] and form.cleaned_data['manager'] or tr.manager,
                    default_tester = form.cleaned_data['update_default_tester'] and form.cleaned_data['default_tester'] or tr.default_tester,
                )

                for tcr in tr.case_run.all():
                    n_tr.add_case_run(
                        case = tcr.case,
                        #assignee = form.cleaned_data['update_assignee'] and form.cleaned_data['assignee'] or tcr.assignee,
                        assignee =  tcr.assignee,
                        case_text_version = (form.cleaned_data['update_case_text'] and
                                             bool(tcr.get_text_versions()) and
                                             tcr.get_text_versions()[0] or
                                             tcr.case_text_version),
                        build = form.cleaned_data['build'],
                        notes = tcr.notes,
                        sortkey = tcr.sortkey,
                    )

                for env_value in tr.env_value.all():
                    n_tr.add_env_value(env_value)

                if form.cleaned_data['clone_cc']:
                    for cc in tr.cc.all():
                        n_tr.add_cc(user = cc)

                if form.cleaned_data['clone_tag']:
                    for tag in tr.tag.all():
                        n_tr.add_tag(tag = tag)

            if len(trs) == 1:
                return HttpResponseRedirect(
                    reverse('tcms.apps.testruns.views.get', args=[n_tr.pk])
                )

            params = {
                'product': form.cleaned_data['product'].pk,
                'product_version': form.cleaned_data['product_version'].pk,
                'build': form.cleaned_data['build'].pk
            }

            return HttpResponseRedirect('%s?%s' % (
                reverse('tcms.apps.testruns.views.all'),
                urllib.urlencode(params, True)
            ))
    else:
        form = MulitpleRunsCloneForm(initial={
            'run': trs.values_list('pk', flat=True),
            'manager': request.user,
            'default_tester': request.user,
            'assignee': request.user,
            'update_manager': False,
            'update_default_tester': True,
            'update_assignee': True,
            'update_case_text': True,
            'clone_cc': True,
            'clone_tag': True,
        })
        form.populate(trs = trs)

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'clone_form': form,
    })

def order_case(request, run_id):
    """
    Resort case with new order
    """
    # Current we should rewrite all of cases belong to the plan.
    # Because the cases sortkey in database is chaos,
    # Most of them are None.

    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    if not request.REQUEST.get('case_run'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one case is required by re-oder in run.',
            next = reverse('tcms.apps.testruns.views.get', args=[run_id, ]),
        ))

    case_run_ids = request.REQUEST.getlist('case_run')
    tcrs = TestCaseRun.objects.filter(case_run_id__in = case_run_ids)

    for tcr in tcrs:
        new_sort_key = (case_run_ids.index(str(tcr.case_run_id)) + 1) * 10
        if tcr.sortkey != new_sort_key:
            tcr.sortkey = new_sort_key
            tcr.save()

    return HttpResponseRedirect(
        reverse('tcms.apps.testruns.views.get', args=[run_id, ])
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
        reverse('tcms.apps.testruns.views.get', args=[run_id, ])
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

    return HttpResponseRedirect(reverse('tcms.apps.testruns.views.get', args=[run_id]))

@user_passes_test(lambda u: u.has_perm('testruns.add_testcaserun'))
def assign_case(request, run_id, template_name="run/assign_case.html"):
    """
    Assign case to run
    """
    SUB_MODULE_NAME = "runs"

    from tcms.apps.testcases.models import TestCasePlan

    try:
        tr = TestRun.objects.select_related('plan', 'manager__email', 'build')
        tr = tr.get(run_id = run_id)
        tp = tr.plan
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
                try:
                    tcp = TestCasePlan.objects.get(plan=tp, case=nc)
                    sortkey = tcp.sortkey
                except ObjectDoesNotExist, error:
                    sortkey = 0
                tr.add_case_run(
                    case = nc,
                    sortkey = sortkey,
                )
        else:
            for nc in ncs:
                tr.add_case_run(
                    case = nc,
                )

        return HttpResponseRedirect(reverse('tcms.apps.testruns.views.get', args=[tr.run_id, ]))

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
                'message': 'The user you typed does not exist in database'
            })
        if request.REQUEST['do'] == 'add':
            tr.add_cc(user = user)

        if request.REQUEST['do'] == 'remove':
            tr.remove_cc(user = user)

    return direct_to_template(request, 'run/get_cc.html', {
        'test_run': tr,
    })

def update_case_run_text(request, run_id):
    """
    Update the IDLE cases to newest text
    """
    from tcms.core.utils import Prompt
    try:
        tr = TestRun.objects.get(run_id = run_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    if request.REQUEST.get('case_run'):
        tcrs = tr.case_run.filter(pk__in = request.REQUEST.getlist('case_run'))
    else:
        tcrs = tr.case_run.all()

    tcrs = tcrs.filter(case_run_status__name = 'IDLE')

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
        next = reverse('tcms.apps.testruns.views.get', args=[run_id,]),
    ))

def export(request, run_id, template_name = 'run/export.csv'):
    import time
    timestamp_str = time.strftime('%Y-%m-%d')
    case_runs = request.REQUEST.getlist('case_run')
    #Export selected case runs
    if case_runs:
        tcrs = TestCaseRun.objects.filter(case_run_id__in = case_runs)
    #Export all case runs
    else:
        tcrs = TestCaseRun.objects.filter(run = run_id)
    response = direct_to_template(request, template_name, {
        'tcrs': tcrs,
    })

    response['Content-Disposition'] = 'attachment; filename=tcms-testcase-runs-%s.csv' % timestamp_str

    return response

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
            if not self.request.user.has_perm('testruns.' + perm + '_tcmsenvrunvaluemap'):
                return {'rc': 1, 'response': 'Permission deined - %s' % perm}

            return False

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

    if not request.REQUEST.get('a') in run_env_actions.__all__:
        ajax_response = {'rc': 1, 'response': 'Unrecognizable actions'}
        return HttpResponse(simplejson.dumps(ajax_response))

    func = getattr(run_env_actions, request.REQUEST['a'])

    try:
        return func()
    except:
        raise

def caseruns(request, templ='report/caseruns.html'):
    '''
    View that search caseruns.
    '''
    from tcms.search.forms import RunForm
    from tcms.search.query import SmartDjangoQuery
    from tcms.apps.testruns.models import TestRun
    queries = request.GET
    r_form = RunForm(queries)
    r_form.populate(queries)
    context = {}
    if r_form.is_valid():
        runs = SmartDjangoQuery(r_form.cleaned_data, TestRun.__name__)
        runs = runs.evaluate()
        caseruns = get_caseruns_of_runs(runs, queries)
        context['test_case_runs'] = caseruns
        context['runs'] = runs
    response = direct_to_template(request, templ, context)
    return response

def get_caseruns_of_runs(runs, kwargs=None):
    '''
    Filtering argument -
        priority
        tester
        plan tag
    '''
    from tcms.apps.testruns.models import TestCaseRun
    if kwargs is None: kwargs = {}
    plan_tag = kwargs.get('plan_tag', None)
    if plan_tag:
        runs = runs.filter(plan__tag__name=plan_tag)
    caseruns = TestCaseRun.objects.filter(run__in=runs)
    priority = kwargs.get('priority', None)
    if priority:
        caseruns = caseruns.filter(case__priority__pk=priority)
    tester = kwargs.get('tester', None)
    if tester:
        caseruns = caseruns.filter(tested_by__pk=tester)
    status = kwargs.get('status', None)
    if status:
        caseruns = caseruns.filter(case_run_status__name__iexact=status)
    return caseruns
