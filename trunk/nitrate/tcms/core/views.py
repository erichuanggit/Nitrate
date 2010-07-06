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

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from tcms.core.utils.raw_sql import RawSQL

from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun
from tcms.testcases.models import TestCase

MODULE_NAME = "index"

def index(request, template_name = 'index.html'):
    """
    Home page of TCMS
    """
    from django.views.generic.simple import direct_to_template
    from django.db.models import Q
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    
    plans_query = {
        'author': request.user,
    }
    
    runs_query = {
        'people': request.user,
        'is_active': True,
        'status': 'running',
    }
    
    tps = TestPlan.list(plans_query)
    tps = tps.order_by('-plan_id')
    tps = tps.select_related('product', 'type')
    tps = tps.extra(select={
        'num_runs': RawSQL.num_runs,
    })
    
    trs = TestRun.list(runs_query)
    
    trs = trs.extra(
        select={
            'completed_case_run_percent': RawSQL.completed_case_run_percent,
            'failed_case_run_percent':RawSQL.failed_case_run_percent,
        },
    )
    
    return direct_to_template(request, template_name, {
        'module': MODULE_NAME,
        'test_plans_count': tps.count(),
        'test_runs_count': trs.count(),
        'last_15_test_plans': tps[:15],
        'last_15_test_runs': trs[:15],
    })

def search(request):
    """
    Redirect to correct url of the search content
    """
    request_content = request.REQUEST.get('search_content', '')
    request_type = request.REQUEST.get('search_type')
    
    # Get search contents
    search_types = {
        'plans': ('testplans', 'testplan', TestPlan, reverse('tcms.testplans.views.all')),
        'runs': ('testruns', 'testrun', TestRun, reverse('tcms.testruns.views.all')),
        'cases': ('testcases', 'testcase', TestCase, reverse('tcms.testcases.views.all'))
    }
    
    search_type = search_types.get(request_type)
    
    app_label = search_type[0]
    model = search_type[1]
    object = search_type[2]
    base_search_url = search_type[3]
    
    # Try to get the object directly
    try:
        request_content = int(request_content)
        
        object = object.objects.get(pk = request_content)
        
        url = '%s?search=%s' % (
            reverse('tcms.%s.views.get' % app_label, args=[object.pk]),
            request_content
        )
        
        return HttpResponseRedirect(url)
    except ObjectDoesNotExist, error:
        pass
    except ValueError:
        pass
    
    # Redirect to search all page
    url = '%s?a=search&search=%s' % (base_search_url, request_content)
    
    return HttpResponseRedirect(url)
