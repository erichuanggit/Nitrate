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

def string_to_list(strs, spliter = ','):
    """Convert the string to list"""
    if isinstance(strs, list):
        str_list = map(lambda t: str(t).strip(), strs)
    else:
        str_list = map(lambda t: str(t).strip(), strs.split(spliter))
    return [s for s in str_list if s]

def form_errors_to_list(form):
    """
    Convert errors of form to list
    
    Use for Ajax.Request response
    """
    return [(k, unicode(v[0])) for k, v in form.errors.items()]


#FIXME: Performance needs to be improved.
#def all_case_combinations(s):
#    if len(s) == 0:
#        yield ""
#    else:
#        for x in all_case_combinations(s[1:]):
#            yield s[0].lower() + x
#            yield s[0].upper() + x

def get_string_combinations(s):
    """
    @param s: string 
    @return: a list containing s and the lowercase, uppercase
            & first letter uppercase form of s.  
    """
    return s, s.lower(), s.upper(), s.capitalize()

