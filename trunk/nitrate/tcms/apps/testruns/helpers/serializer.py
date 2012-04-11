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
A serializer to import/export between model objects and file formats.
'''

import csv
from lxml import etree

class TCR2File(object):
    '''
    Write TestCaseRun queryset into CSV or XML.
    '''
    ROOT = 'testcaseruns'
    HEADERS = ("Case Run ID", "Case ID",
        "Category", "Status", "Summary",
        "script", "Automated", "Log Link",
        "Bug IDs")

    def __init__(self, tcrs):
        self.root = self.ROOT
        self.headers = self.HEADERS
        self.tcrs = tcrs
        self.rows = []

    def tcr_attrs_in_a_list(self, tcr):
        line = [
            tcr.pk, tcr.case.pk, tcr.case.category,
            tcr.case_run_status, tcr.case.summary.encode('utf-8'),
            tcr.case.script, tcr.case.is_automated,
            self.log_links(tcr), self.bug_ids(tcr)
        ]
        return line

    def log_links(self, tcr):
        '''
        Wrap log links into a single cell by
        joining log links.
        '''
        return 'N/A'

    def bug_ids(self, tcr):
        '''
        Wrap bugs into a single cell by
        joining bug IDs.
        '''
        return ' '.join(
            tcr.case.case_bug.values_list('pk', flat=True)
        )

    def tcrs_in_rows(self):
        if self.rows: return self.rows
        for tcr in self.tcrs:
            row = self.tcr_attrs_in_a_list(tcr)
            self.rows.append(row)
        return self.rows

    def write_to_csv(self, fileobj):
        writer = csv.writer(fileobj)
        rows = self.tcrs_in_rows()
        writer.writerow(self.headers)
        writer.writerows(rows)

    def write_to_xml(self, fileobj):
        root = etree.Element(self.root)
        attr_keys = [
            k.lower().replace(' ', '_')
            for k in self.headers
        ]
        for row in self.tcrs_in_rows():
            sub_elem = etree.Element('testcaserun')
            count = 0
            for k, v in zip(attr_keys, row):
                try:
                    sub_elem.set(k, '%s' % str(v))
                except ValueError:
                    pass
            root.append(sub_elem)
        fileobj.write(etree.tostring(root))