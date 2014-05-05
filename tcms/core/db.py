# -*- coding: utf-8 -*-
#
# Nitrate is copyright 2014 Red Hat, Inc.
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
#   Chenxiong Qi <cqi@redhat.com>

from django.db import connection
from itertools import izip

__all__ = ('execute_sql',)


def execute_sql(sql, *params):
    cursor = connection.cursor()
    cursor.execute(sql, params)
    field_names = [field[0] for field in cursor.description]
    while 1:
        row = cursor.fetchone()
        if row is None:
            break
        yield dict(izip(field_names, row))


# FIXME: migrate execute_sql to SQLExecution class


class SQLExecution(object):
    '''Cursor.execute proxy class

    This proxy class provides two major abitlities.

    1. iteration of visiting each row selected by SELECT statement from db
    server.

    2. get the affected rows' count. This will benefit developers to avoid
    issuing extra SQL to count the number of rows current SELECT statement is
    retrieving.

    Compatibility: the second item above relies on cursor.rowcount attribute
    described in PEP-0249. Cannot guarantee all database backends supports this
    by following 249 specificiation. But, at least, MySQLdb and psycopg2 does.
    '''

    def __init__(self, sql, params):
        self.cursor = connection.cursor()
        self.cursor.execute(sql, params)
        self.field_names = [field[0] for field in self.cursor.description]

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def rows(self):
        while 1:
            row = self.cursor.fetchone()
            if row is None:
                break
            yield dict(izip(self.field_names, row))
