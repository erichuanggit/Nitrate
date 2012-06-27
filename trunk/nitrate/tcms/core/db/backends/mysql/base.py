#!/usr/bin/env python
# Author: Chaobin Tang <ctang@redhat.com>

'''
IMPORTANT!
This MySQL database backend is backend
derived from Django mysql backend, with only
one difference, that it looks at every
query sent to the cursor to check if
this is a deletion on the table called
'test_case_texts'.
This is a depressing solution to the problem
https://bugzilla.redhat.com/show_bug.cgi?id=713662
after we failed to ascertain the root cause
regardless of the collaboration with eng-ops.
In this backend, these things happen in addition to
all default behaviors that a backend should have -
1. It checks if a query is a deletion on table
'test_case_texts';
2. If it does, it logs down this query, user that
fired this http request, and it sends email to the
ADMIN defined in settings;
3. Following step 2, it will raise SuspiciousOperation
so that this query will not be executed.
'''


from django.db.backends.mysql.base import DatabaseWrapper as MySQLWrapper,\
CursorWrapper as MySQLCursorWrapper
from tcms.core.db.backends.mysql import monitor


class DatabaseWrapper(MySQLWrapper):

    def _cursor(self):
        cursor = CursorWrapper(self.connection)
        cursor = super(DatabaseWrapper, self)._cursor()
        return CursorWrapper(cursor.cursor)

class CursorWrapper(MySQLCursorWrapper):

    def execute(self, query, args=None):
        if monitor.ON:
            monitor.watchit(query, args)
        super(self.__class__, self).execute(query, args)