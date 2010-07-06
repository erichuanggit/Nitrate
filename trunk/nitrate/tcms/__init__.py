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

VERSION = (3, 0, 3, 'final', 2, True)
XMLRPC_VERSION = (0, 1, 1, 'final', 2)

def get_version():
    import os.path.dirname
    from django.utils.version import get_svn_revision
    
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version += '.%s' % VERSION[2]
    else:
        if VERSION[3] != 'final':
            version += ' %s%s' % (VERSION[3], VERSION[4])
    
    svn_rev = get_svn_revision(os.path.dirname(__file__))
    if svn_rev != u'SVN-unknown':
        version = "%s %s" % (version, svn_rev)
    return version

def is_release():
    return VERSION[5]
