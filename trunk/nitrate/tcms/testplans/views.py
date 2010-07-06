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

from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist
from tcms.core.utils import Prompt
from tcms.core.utils.raw_sql import RawSQL

from tcms.core.models import TCMSLog
from tcms.management.models import Product

from models import TestPlan

MODULE_NAME = "testplans"

@user_passes_test(lambda u: u.has_perm('testplans.add_testplan'))
def new(request, template_name = 'plan/new.html'):
    from forms import NewPlanForm
    from tcms.management.models import TCMSEnvGroup

    SUB_MODULE_NAME = "new_plan"

    # If the form has been submitted...
    if request.method == 'POST':

        # A form bound to the POST data
        form = NewPlanForm(request.POST, request.FILES)
        form.populate(product_id = request.REQUEST.get('product'))

        # Process the upload plan document
        if form.is_valid():
            if form.cleaned_data.get('upload_plan_text'):
                # Set the summary form field to the uploaded text
                form.data['summary'] = form.cleaned_data['summary']

                # Generate the form
                return direct_to_template(request, template_name, {
                    'module': MODULE_NAME,
                    'sub_module': SUB_MODULE_NAME,
                    'form' : form,
                })

        # Process the test plan submit to the form
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data        
            # Create test plan content
            tp = TestPlan.objects.create(
                product = form.cleaned_data['product'],
                author = request.user,
                default_product_version = form.cleaned_data['default_product_version'],
                type = form.cleaned_data['type'],
                name = form.cleaned_data['name'],
                create_date = datetime.now(),
                extra_link = form.cleaned_data['extra_link']
            )

            # Add test plan text
            if request.user.has_perm('testplans.add_testplantext'):
                tp.add_text(
                    author = request.user,
                    plan_text = form.cleaned_data['summary']
                )

            # Add tag to plan
            #if request.user.has_perm('testplans.add_testplantag'):
            #    for tag in form.cleaned_data['tag']:
            #        tp.add_tag(
            #            tag = tag
            #        )

            # Add test plan environment groups
            if request.user.has_perm('management.add_tcmsenvplanmap'):
                if request.REQUEST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in = request.REQUEST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(env_group = env_group)

            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get', args = [tp.plan_id, ])
            )
    else:
        form = NewPlanForm() # An unbound form

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form' : form,
    })

@user_passes_test(lambda u: u.has_perm('testplans.delete_testplan'))
def delete(request, plan_id):
    if request.GET.get('sure', 'no') == 'no':
        return HttpResponse("\
            <script>if(confirm('Are you sure you want to delete this plan %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) { \
                window.location.href='%s?sure=yes' \
            } else { \
                history.go(-1) \
            };</script>" % (plan_id, reverse(
                'tcms.testplans.views.delete', args = [plan_id, ]
            ))
        )
    elif request.GET.get('sure') == 'yes':
        try:
            tp = TestPlan.objects.get(plan_id = plan_id)
        except ObjectDoesNotExist, error:
            raise Http404

        try:
            tp.delete()
            return HttpResponse("<script>window.location.href='%s'</script>" % reverse(
                'tcms.testplans.views.all')
            )
        except:
            return HttpResponse("<script>alert('Delete failed');history.go(-1);</script>")
    else:
        return HttpResponse("<script>alert('Nothing yet');history.go(-1);</script>")

def all(request, template_name = 'plan/all.html'):
    from forms import SearchPlanForm

    # Define the default sub module
    SUB_MODULE_NAME = 'plans'

    # If it's not a search the page will be blank
    tps = None
    query_result = False

    # if it's a search request the page will be fill
    if request.REQUEST.items():
        search_form = SearchPlanForm(request.REQUEST)
        if request.REQUEST.get('product'):
            search_form.populate(product_id = request.REQUEST['product'])
        else:
            search_form.populate()

        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub module value
            if request.REQUEST.get('author'):
                if request.user.is_authenticated():
                    if request.REQUEST['author'] == request.user.username \
                    or request.REQUEST['author'] == request.user.email:
                        SUB_MODULE_NAME = "my_plans"

            query_result = True
            # build a QuerySet:
            tps = TestPlan.list(search_form.cleaned_data)
            tps = tps.select_related('author', 'type', 'product')

            # We want to get the number of cases and runs, without doing
            # lots of per-test queries.
            # 
            # Ideally we would get the case/run counts using m2m field tricks
            # in the ORM
            # Unfortunately, Django's select_related only works on ForeignKey
            # relationships, not on ManyToManyField attributes
            # See http://code.djangoproject.com/ticket/6432

            # SQLAlchemy can handle this kind of thing in several ways.
            # Unfortunately we're using Django

            # The cleanest way I can find to get it into one query is to
            # use QuerySet.extra()
            # See http://docs.djangoproject.com/en/dev/ref/models/querysets
            tps = tps.extra(select = {
                'num_cases': RawSQL.num_cases,
                'num_runs': RawSQL.num_runs,
            })
    else:

        # Set search active plans only by default
        # I wish to use 'default' argument, as the same as in ModelForm
        # But it looks does not work
        search_form = SearchPlanForm(initial = { 'is_active': True })

    if request.REQUEST.get('action') == 'clone_case':
        template_name = 'case/clone_select_plan.html'
        tps = tps.order_by('name')

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plans' : tps,
        'query_result' : query_result,
        'search_plan_form' : search_form,
    })

def get(request, plan_id, template_name = 'plan/get.html'):
    """
    Display the plan details
    """
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id = plan_id)
        tp.latest_text = tp.latest_text()
    except ObjectDoesNotExist, error:
        if request.REQUEST.get('type') == 'preview_html':
            return direct_to_template(
                request, 'plan/get_preview_not_found.html'
            )

        raise Http404

    if request.REQUEST.get('type') == 'preview_html':
        return direct_to_template(request, 'plan/get_preview.html', {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'test_plan': tp,
        })

    # Generate the attachment list of plan
    tp_attachments = tp.attachment.all()

    # Generate the run list of plan
    tp_trs = tp.run.select_related('build', 'manager', 'default_tester')
    # Further optimize by adding caserun attributes:
    tp_trs = tp_trs.extra(
        select = {
        'total_num_caseruns': RawSQL.total_num_caseruns,
        'completed_case_run_percent': RawSQL.completed_case_run_percent,
        'failed_case_run_percent':RawSQL.failed_case_run_percent,
        },
    )

    tp_rvs = tp.review.select_related('author', 'default_reviewer')
    tp_rvs = tp_rvs.extra(
        select = {
            'total_num_review_cases': RawSQL.total_num_review_cases,
        }
    )

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'test_runs': tp_trs,
        'test_reviews': tp_rvs,
    })

@user_passes_test(lambda u: u.has_perm('testplans.change_testplan'))
def edit(request, plan_id, template_name = 'plan/edit.html'):
    """
    Edit test plan view
    """
    from forms import EditPlanForm
    from tcms.management.models import TCMSEnvGroup, Version
    # Define the default sub module
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id = plan_id)
    except ObjectDoesNotExist, error:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        from datetime import datetime
        form = EditPlanForm(request.REQUEST)
        if request.REQUEST.get('product'):
            form.populate(product_id = request.REQUEST['product'])
        else:
            form.populate()

        #FIXME: Error handle
        if form.is_valid():
            if request.user.has_perm('testplans.change_testplan'):
                tp.name = form.cleaned_data['name']
                tp.product = form.cleaned_data['product']
                tp.default_product_version = form.cleaned_data['default_product_version']
                tp.type = form.cleaned_data['type']
                tp.is_active = form.cleaned_data['is_active']
                tp.extra_link = form.cleaned_data['extra_link']
                tp.save()

            if request.user.has_perm('testplans.add_testplantext'):
                if not tp.latest_text() or request.REQUEST.get('summary') != tp.latest_text().plan_text:
                    tp.add_text(
                        author = request.user,
                        plan_text = request.REQUEST.get('summary')
                    )

            if request.user.has_perm('management.change_tcmsenvplanmap'):
                tp.clear_env_groups()

                if request.REQUEST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in = request.REQUEST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(
                            env_group = env_group
                        )

            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get', args = [plan_id, ])
            )
    else:
        # Generate a blank form
        # Temporary use one environment group in this case
        if tp.env_group.all():
            for env_group in tp.env_group.all():
                env_group_id = env_group.id
                break
        else:
            env_group_id = None

        form = EditPlanForm(initial = {
            'name': tp.name,
            'product': tp.product_id,
            'product_version': tp.get_version_id(),
            'type': tp.type_id,
            'summary': tp.latest_text() and tp.latest_text().plan_text or '',
            'env_group': env_group_id,
            'is_active': tp.is_active,
            'extra_link': tp.extra_link,
        })
        form.populate(product_id = tp.product_id)

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'form': form,
        #'env_properties': testplan_env_properties,
    })

def printable(request, plan_id, template_name = 'plan/printable.html'):
    try:
        plan = TestPlan.objects.get(plan_id = plan_id)
    except ObjectDoesNotExist:
        raise Http404

    cases = plan.case.all()

    if request.REQUEST.get('case'):
        cases = cases.filter(case_id__in = request.REQUEST.getlist('case'))

    return direct_to_template(request, template_name, {
        'plan': plan,
        'cases': cases,
        'latest_html': plan.latest_text().plan_text
    })

@user_passes_test(lambda u: u.has_perm('testplans.add_testplan'))
def clone(request, template_name = 'plan/clone.html'):
    from tcms.testcases.models import TestCase
    from forms import ClonePlanForm

    SUB_MODULE_NAME = 'plans'

    if not request.REQUEST.get('plan_id'):
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'At least one plan is required by clone function.',
            next = 'javascript:window.history.go(-1)',
        ))

    tps = TestPlan.objects.filter(plan_id__in = request.REQUEST.getlist('plan_id'))

    if not tps:
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Info,
            info = 'The plan you specific is not exist in database',
            next = 'javascript:window.history.go(-1)',
        ))

    # Clone the plan if the form is submitted
    if request.method == "POST":
        clone_form = ClonePlanForm(request.REQUEST)
        clone_form.populate(product_id = request.REQUEST.get('product_id'))
        if clone_form.is_valid():
            from datetime import datetime
            from urllib import urlencode

            # Create new test plan.
            for tp in tps:
                tp_dest = TestPlan.objects.create(
                    product = clone_form.cleaned_data['product'],
                    author = clone_form.cleaned_data['keep_orignal_author'] and tp.author or request.user,
                    type = tp.type,
                    default_product_version = clone_form.cleaned_data['default_product_version'],
                    name = len(tps) == 1 and clone_form.cleaned_data['name'] or tp.name,
                    create_date = tp.create_date,
                    is_active = tp.is_active,
                    extra_link = tp.extra_link,
                )

                # Copy the plan documents
                if clone_form.cleaned_data['copy_texts']:
                    tptxts_src = tp.text.all()
                    for tptxt_src in tptxts_src:
                        tp_dest.add_text(
                            plan_text_version = tptxt_src.plan_text_version,
                            author = tptxt_src.author,
                            create_date = tptxt_src.create_date,
                            plan_text = tptxt_src.plan_text,
                        )
                else:
                    tp_dest.add_text(
                        author = request.user,
                        plan_text = '',
                    )

                # Copy the plan tags
                for tp_tag_src in tp.tag.all():
                    tp_dest.add_tag(tag = tp_tag_src)

                # Copy the plan attachments
                if clone_form.cleaned_data['copy_attachements']:
                    for tp_attach_src in tp.attachment.all():
                        tp_dest.add_attachment(attachment = tp_attach_src)

                # Copy the environment group
                if clone_form.cleaned_data['copy_environment_group']:
                    for env_group in tp.env_group.all():
                        tp_dest.add_env_group(env_group = env_group)

                # Link the cases of the plan
                if clone_form.cleaned_data['link_testcases']:
                    tpcases_src = tp.case.all()

                    if clone_form.cleaned_data['copy_testcases']:
                        for tpcase_src in tpcases_src:
                            if clone_form.cleaned_data['maintain_case_orignal_author']:
                                author = tpcase_src.author
                            else:
                                author = request.user

                            if clone_form.cleaned_data['keep_case_default_tester']:
                                default_tester = tpcase_src.default_tester
                            else:
                                default_tester = request.user

                            tpcase_dest = TestCase.objects.create(
                                create_date = tpcase_src.create_date,
                                is_automated = tpcase_src.is_automated,
                                sortkey = tpcase_src.sortkey,
                                script = tpcase_src.script,
                                arguments = tpcase_src.arguments,
                                summary = tpcase_src.summary,
                                requirement = tpcase_src.requirement,
                                alias = tpcase_src.alias,
                                estimated_time = tpcase_src.estimated_time,
                                case_status = tpcase_src.case_status,
                                category = tpcase_src.category,
                                priority = tpcase_src.priority,
                                author = author,
                                default_tester = default_tester,
                            )

                            for tc_tag_src in tpcase_src.tag.all():
                                tpcase_dest.add_tag(tag = tc_tag_src)
                            for component in tpcase_src.component.filter(product__id = tp.product_id):
                                try:
                                    new_c = tp_dest.product.component.get(
                                        name = component.name
                                    )
                                except ObjectDoesNotExist, error:
                                    new_c = tp_dest.product.component.create(
                                        name = component.name,
                                        initial_owner = request.user,
                                        description = component.description,
                                    )

                                tpcase_dest.add_component(new_c)

                            text = tpcase_src.latest_text()

                            if text:
                                tpcase_dest.add_text(
                                    author = text.author,
                                    action = text.action,
                                    effect = text.effect,
                                    setup = text.setup,
                                    breakdown = text.breakdown,
                                    create_date = text.create_date,
                                )

                            tp_dest.add_case(case = tpcase_dest)
                    else:
                        for tpcase_src in tpcases_src:
                            tp_dest.add_case(case = tpcase_src)

            if len(tps) == 1:
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get', args = [tp_dest.plan_id, ])
                )
            else:
                args = {
                    'action': 'search',
                    'product': form.cleaned_data['product'].id,
                    'product_version': form.cleaned_data['default_product_version'].id,
                }

                url_args = urlencode(args)

                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.all') + '?' + url_args
                )
    else:
        # Generate the default values for the form
        if len(tps) == 1:
            clone_form = ClonePlanForm(initial = {
                'product': tps[0].product.id,
                'product_version': tps[0].get_version_id(),
                'copy_texts': True,
                'copy_attachements': True,
                'copy_environment_group': True,
                'link_testcases': True,
                'copy_testcases': True,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': True,
                'name': 'Copy of %s' % tps[0].name
            })
            clone_form.populate(product_id = tps[0].product.id)
        else:
            clone_form = ClonePlanForm(initial = {
                'copy_texts': True,
                'copy_attachements': True,
                'link_testcases': True,
                'copy_testcases': True,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': True,
            })

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplans': tps,
        'clone_form': clone_form,
    })

def export(request, plan_id, template_name = 'plan/export.xml'):
    """Export the plan"""
    from datetime import datetime

    try:
        tp = TestPlan.objects.select_related().get(plan_id = plan_id)
    except ObjectDoesNotExist, error:
        raise Http404

    if request.REQUEST.get('case'):
        tcs = tp.case.filter(case_id__in = request.REQUEST.getlist('case'))
    else:
        tcs = tp.case.all()

    timestamp = datetime.now()
    timestamp_str = '%02i-%02i-%02i' \
        % (timestamp.year, timestamp.month, timestamp.day)

    response = direct_to_template(request, template_name, {
        'test_plan': tp,
        'test_cases': tcs,
    })

    response['Content-Disposition'] = 'attachment; filename=tcms-testcases-%s.xml' % timestamp_str

    return response

def attachment(request, plan_id, template_name = 'plan/attachment.html'):
    """Manage attached files"""
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp ,
    })

def text_history(request, plan_id, template_name = 'plan/history.html'):
    """View test plan text history"""
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except ObjectDoesNotExist, error:
        raise Http404(error)

    tptxts = tp.text.all()
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'test_plan_texts': tptxts,
        'select_plan_text_version': int(
            request.REQUEST.get('plan_text_version', 0)
        ),
    })

def cases(request, plan_id):
    """Process the xml with import"""
    from django.utils.simplejson import dumps as json_dumps
    from tcms.core.utils import Prompt
    from tcms.testcases.models import TestCase, TestCaseCategory, TestCaseTag
    from tcms.testcases.models import TestCaseText, TestCaseStatus
    from tcms.management.models import TestTag
    
    ajax_response = { 'response': 'ok' }
    
    class CaseActions(object):
        def __init__(self, request, tp):
            self.__all__ = [
                'link_cases', 'delete_cases', 'order_cases', 'import_cases'
            ]
            self.request = request
            self.tp = tp
        
        def link_cases(self, template_name = 'plan/search_case.html'):
            """
            Handle to form to add case to plans.
            """
            from tcms.testcases.forms import SearchCaseForm
            
            SUB_MODULE_NAME = 'plans'
            tcs = None
            
            if request.REQUEST.get('action') == 'add_to_plan':
                if request.user.has_perm('testcases.add_testcaseplan'):
                    tcs = TestCase.objects.filter(case_id__in = request.REQUEST.getlist('case'))
                    
                    for tc in tcs:
                        tp.add_case(case = tc)
                else:
                    return HttpResponse("Permission Denied")
                
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.get', args = [plan_id, ])
                )
            
            if request.REQUEST.get('action') == 'search':
                form = SearchCaseForm(request.REQUEST)
                if form.is_valid():
                    tcs = TestCase.list(form.cleaned_data)
                    tcs = tcs.select_related(
                        'author', 'default_tester', 'case_status',
                        'priority', 'category', 'tag__name'
                    )
                    tcs = tcs.exclude(case_id__in = tp.case.values_list(
                        'case_id', flat = True
                    ))
            else:
                form = SearchCaseForm(initial = {
                    'product': tp.product_id,
                    'product_version': tp.get_version_id(),
                    'case_status_id': TestCaseStatus.get_CONFIRMED()
                })
            
            return direct_to_template(request, template_name, {
                'module': MODULE_NAME,
                'sub_module': SUB_MODULE_NAME,
                'test_plan': tp,
                'test_cases': tcs,
                'search_form': form,
            })
        
        def delete_cases(self):
            try:
                tp = TestPlan.objects.get(plan_id = plan_id)
            except TestPlan.DoesNotExist:
                raise Http404
            
            if not request.REQUEST.get('case'):
                ajax_response['reponse'] = 'At least one case is required to delete.'
                return HttpResponse(json_dumps(ajax_response))
            
            tcs = TestCase.objects.filter(case_id__in = request.REQUEST.getlist('case'))
            
            # Log Action
            tp_log = TCMSLog(model = tp)
            
            for tc in tcs:
                tp_log.make(
                    who = request.user,
                    action = 'Remove case %s from plan %s' % (tc.case_id, tp.plan_id)
                )
                
                tc.log_action(
                    who = request.user,
                    action = 'Remove from plan %s' % tp.plan_id
                )
                
                tp.delete_case(case = tc)
            
            return HttpResponse(json_dumps(ajax_response))
        
        def order_cases(self):
            """
            Resort case with new order
            """
            # Current we should rewrite all of cases belong to the plan.
            # Because the cases sortkey in database is chaos,
            # Most of them are None.
            try:
                tp = TestPlan.objects.get(plan_id = plan_id)
            except ObjectDoesNOtExist, error:
                raise Http404(error)
            
            if not request.REQUEST.get('case'):
                return HttpResponse(Prompt.render(
                    request = request,
                    info_type = Prompt.Info,
                    info = 'At least one case is required by re-oder in plan.',
                    next = reverse('tcms.testplans.views.get', args = [plan_id, ]),
                ))
            
            tc_ids = request.REQUEST.get('case').split(',')
            tcs = TestCase.objects.filter(case_id__in = tc_ids)
            
            for tc in tcs:
                new_sort_key = (tc_ids.index(str(tc.case_id)) + 1) * 10
                if tc.sortkey != new_sort_key:
                    tc.sortkey = new_sort_key
                    tc.save()
            
            return HttpResponseRedirect(
                reverse('tcms.testplans.views.get', args = [plan_id, ])
            )
        
        def import_cases(self):
            from forms import ImportCasesViaXMLForm
            
            if request.method == 'POST':
                # Process import case from XML action
                if not request.user.has_perm('testcases.add_testcaseplan'):
                    return HttpResponse(Prompt.render(
                        request = request,
                        info_type = Prompt.Alert,
                        info = 'Permission denied',
                        next = reverse('tcms.testplans.views.get', args = [plan_id, ]),
                    ))
                
                xml_form = ImportCasesViaXMLForm(request.REQUEST, request.FILES)
                
                if xml_form.is_valid():
                    i = 0
                    for case in xml_form.cleaned_data['xml_file']:
                        i += 1
                        
                        # Get the case category from the case and related to the product of the plan
                        try:
                            category = TestCaseCategory.objects.get(
                                product = tp.product, name = case['category_name']
                            )
                        except TestCaseCategory.DoesNotExist:
                            category = TestCaseCategory.objects.create(
                                product = tp.product, name = case['category_name']
                            )
                        
                        # Start to create the objects
                        tc = TestCase.objects.create(
                            is_automated = case['is_automated'],
                            sortkey = i * 10,
                            script = None,
                            arguments = None,
                            summary = case['summary'],
                            requirement = None,
                            alias = None,
                            estimated_time = '0:0:0',
                            case_status_id = case['case_status_id'],
                            category_id = category.id,
                            priority_id = case['priority_id'],
                            author_id = case['author_id'],
                            default_tester_id = case['default_tester_id'],
                        )
                        
                        tc.add_text(
                            case_text_version = 1,
                            author = case['author'],
                            action = case['action'],
                            effect = case['effect'],
                            setup = case['setup'],
                            breakdown = case['breakdown'],
                        )
                        
                        #handle tags
                        if case['tags']:
                            for tag in case['tags']:
                                tc.add_tag(tag = tag)
                        
                        tc.add_to_plan(plan = tp)
                    
                    return HttpResponseRedirect(reverse('tcms.testplans.views.get', args = [plan_id, ]) + '#testcases')
                else:
                    return HttpResponse(Prompt.render(
                        request = request,
                        info_type = Prompt.Alert,
                        info = xml_form.errors,
                        next = reverse('tcms.testplans.views.get', args = [plan_id, ]) + '#testcases'
                    ))
            else:
                return HttpResponseRedirect(reverse('tcms.testplans.views.get', args = [plan_id, ]) + '#testcases')
    
    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except ObjectDoesNotExist, error:
        raise Http404
    
    cas = CaseActions(request, tp)
    actions = request.REQUEST.get('a')
    
    if not actions in cas.__all__:
        message = 'Unrecognizable actions'
        if request.REQUEST.get('format') == 'json':
            ajax_response = {'rc': 1, 'response': message}
            return HttpResponse(simplejson.dumps(ajax_response))
        
        return HttpResponse(Prompt.render(
            request = request,
            info_type = Prompt.Alert,
            info = message,
            next = reverse('tcms.testplans.views.get', args = [plan_id, ]),
        ))
        
    
    func = getattr(cas, actions)
    return func()

def component(request, template_name = 'plan/get_component.html'):
    """
    Manage the component template for plan
    
    Parameters:
      plan - Necessary, to determine which plan you need to modify the
             component template
      a - Optional, Actions for the plan, now it have 'add', 'remove', 'update' 
          and 'render' actions. 'render' is default, use for render the page. 
          'update' is use for clean the components then add the new components
          you specific.
      component - Optional, The component ID you wish to operate.
      multiple - Optional, When you modify multiple, the parameter need to 
                 post. It will response a JSON not a page.
    
    Returns:
      HTML page by default, or a JSON when the 'multiple' parameter specific.
    """
    from tcms.management.models import Component
    from models import TestPlanComponent
    
    ajax_response = { 'rc': 0, 'response': 'ok' }
    
    class ComponentActions(object):
        def __init__(self, request, tps, cs):
            self.__all__ = ['add', 'clear', 'remove', 'update', 'render']
            self.__msgs__ = {
                'permission_denied': { 'rc': 1, 'response': 'Permisson denied' },
            }
            
            self.request = request
            self.tps = tps  # Initial TestPlans
            self.cs = cs    # Initial Components
        
        def add(self):
            if not self.request.user.has_perm('testplans.add_testplancomponent'):
                if self.is_ajax():
                    return HttpResponse(simplejson.dumps(self.__msgs__['permission_denied']))
                
                return self.render(message = self.__msgs__['permission_denied']['response'])
            
            for tp in self.tps:
                for c in cs:
                    try:
                        tp.add_component(c)
                    except:
                        raise
            return self.render()
        
        def remove(self):
            if not self.request.user.has_perm('testplans.delete_testplancomponent'):
                if self.is_ajax():
                    return HttpResponse(simplejson.dumps(self.__msgs__['permission_denied']))
                
                return self.render(message = self.__msgs__['permission_denied']['response'])
            
            for tp in self.tps:
                for c in cs:
                    try:
                        tp.remove_component(c)
                    except:
                        raise
            
            return self.render()
        
        def clear(self):
            if not self.request.user.has_perm('testplans.delete_testplancomponent'):
                pass
            
            # Remove the exist components
            TestPlanComponent.objects.filter(
                plan__in = self.tps,
            ).delete()
        
        def update(self):
            self.clear()
            self.add()
            return self.render()
        
        def render(self, message = None):
            if request.REQUEST.get('multiple'):
                return HttpResponse(simplejson.dumps(ajax_response))
            
            return direct_to_template(request, template_name, {
                'test_plan': self.tps[0],
            })
    
    if not request.REQUEST.get('plan'):
        raise Http404
    
    tps = TestPlan.objects.filter(pk__in = request.REQUEST.getlist('plan'))
    cs = Component.objects.filter(pk__in = request.REQUEST.getlist('component'))
    
    cas = ComponentActions(request = request, tps = tps, cs = cs)
    
    action = getattr(cas, request.REQUEST.get('a', 'render'))
    return action()
