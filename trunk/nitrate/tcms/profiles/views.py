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
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm

from models import UserProfile

@login_required
@csrf_protect
def profile(request, username = None, template_name = 'profile/info.html'):
    """
    Edit the profiles of the user
    """
    from forms import UserProfileForm
    
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
