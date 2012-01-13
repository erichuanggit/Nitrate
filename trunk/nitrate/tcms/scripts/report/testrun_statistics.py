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
#   Chaobin Tang <ctang@redhat.com>

'''
TestRun statistics function.
'''

from django.db import connection
from tcms.testruns.models import TestRun

def get_run_with_the_most_caseruns():
    sql = '''
            select run_id, count(run_id) from test_case_runs
            group by run_id order by count(run_id) limit 1
          ''' 
    # cursor