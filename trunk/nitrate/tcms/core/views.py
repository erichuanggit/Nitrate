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

MODULE_NAME = "index"

def index(request, template_name = 'index.html'):
    """
    Home page of TCMS
    """
    from django.views.generic.simple import direct_to_template
    from django.db.models import Q
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
    
    return HttpResponseRedirect(
        reverse('tcms.profiles.views.recent', args=[request.user.username])
    )

def search(request):
    """
    Redirect to correct url of the search content
    """
    from django.db import models
    from django.core.exceptions import ObjectDoesNotExist
    
    qcontent = request.REQUEST.get('tq', '') # Search content
    ctype = request.REQUEST.get('content_type') # Content type
    
    # Get search contents
    app_label = ctype.split('.')[0]
    model = ctype.split('.')[1]
    base_search_url = reverse('tcms.%s.views.all' % app_label)
    
    # Try to get the object directly
    try:
        qcontent = int(qcontent)
        target = models.get_model(*[app_label, model])._default_manager.get(pk=qcontent)
        url = '%s?tq=%s' % (
            reverse('tcms.%s.views.get' % app_label, args=[target.pk]),
            qcontent
        )
        
        return HttpResponseRedirect(url)
    except ObjectDoesNotExist, error:
        pass
    except ValueError:
        pass
    
    # Redirect to search all page
    url = '%s?a=search&tq=%s' % (base_search_url, qcontent)
    return HttpResponseRedirect(url)
