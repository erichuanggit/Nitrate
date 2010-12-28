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

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm

MODULE_NAME = 'profile'

#@user_passes_test(lambda u: u.username == username)
@login_required
def bookmark(request, username, template_name = 'profile/bookmarks.html'):
    """
    Bookmarks for the user
    """
    from django.conf import settings
    from django.utils import simplejson
    
    from forms import BookmarkForm
    from models import BookmarkCategory, Bookmark
    
    if username != request.user.username:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    else:
        up = {'user': request.user}
    
    class BookmarkActions(object):
        def __init__(self):
            self.ajax_response = {
                'rc': 0,
                'response': 'ok',
            }
        
        def add(self):
            form = BookmarkForm(request.REQUEST)
            if not form.is_valid():
                ajax_response = {
                    'rc': 1,
                    'response': form.errors,
                }
                return HttpResponse(simplejson.dumps(ajax_response))
            
            form.save()
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def add_category(self):
            pass
        
        def remove(self):
            pks = request.REQUEST.getlist('pk')
            bks = Bookmark.objects.filter(
                pk__in = pks,
                user = request.user,
            )
            bks.delete()
            
            return HttpResponse(simplejson.dumps(self.ajax_response))
        
        def render(self):
            if request.REQUEST.get('category'):
                bks = Bookmark.objects.filter(
                    user = request.user,
                    category_id = request.REQUEST['category']
                )
            else:
                bks = Bookmark.objects.filter(user = request.user)
            
            return direct_to_template(request, template_name, {
                'user_profile': up,
                'bookmarks': bks,
            })
        
        def render_form(self):
            query = request.GET.copy()
            query['a'] = 'add'
            form = BookmarkForm(initial=query)
            form.populate(user = request.user)
            return HttpResponse(form.as_p())
    
    action = BookmarkActions()
    func = getattr(action, request.REQUEST.get('a', 'render'))
    return func()

@login_required
@csrf_protect
def profile(request, username, template_name = 'profile/info.html'):
    """
    Edit the profiles of the user
    """
    from forms import UserProfileForm
    from models import UserProfile
    
    try:
        u = User.objects.get(username = username)
    except ObjectDoesNotExist, error:
        raise Http404(error)
    
    try:
        up = u.get_profile()
    except ObjectDoesNotExist, error:
        up = u.profile.create()
    
    form = UserProfileForm(instance=up)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=up)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse(
                    'tcms.profiles.views.profile',
                    args=[form.cleaned_data['username']]
                )
            )
    
    return direct_to_template(request, template_name, {
        'user_profile': up,
        'form': form
    })

@login_required
def recent(request, username, template_name='profile/recent.html'):
    """
    List the recent plan/run.
    """
    from tcms.testplans.models import TestPlan
    from tcms.testruns.models import TestRun
    from tcms.testcases.models import TestCase
    from tcms.core.utils.raw_sql import RawSQL
    
    if username != request.user.username:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    else:
        up = {'user': request.user}
    
    plans_query = {
        'author__username': request.user.username,
        'is_active': True,
    }
    
    runs_query = {
        'people_type': 'people',
        'people': request.user,
        'stop_date__isnull': 1,
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
        'user_profile': up,
        'test_plans_count': tps.count(),
        'test_runs_count': trs.count(),
        'last_15_test_plans': tps[:15],
        'last_15_test_runs': trs[:15],
    })

@login_required
def redirect_to_profile(request):
    return HttpResponseRedirect(reverse('tcms.profiles.views.recent', args=[request.user.username]))
