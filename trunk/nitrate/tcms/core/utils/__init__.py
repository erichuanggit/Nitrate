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

from mailto import *
from prompt import *

def string_to_list(tags, spliter = ','):
    """Convert the string to list"""
    if isinstance(tags, list):
        tag_list = map(lambda t: str(t).strip(), tags)
    else:
        tag_list = map(lambda t: str(t).strip(), tags.split(spliter))
    del tags
    return [t for t in tag_list if t]

def form_errors_to_list(form):
    """
    Convert errors of form to list
    
    Use for Ajax.Request response
    """
    return [(k, unicode(v[0])) for k, v in form.errors.items()]
