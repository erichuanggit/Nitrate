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
#   Chenxiong Qi <cqi@redhat.com>

'''
A serializer to import/export between model objects and file formats.
'''

import csv

from xml.sax.saxutils import escape


def escape_entities(text):
    '''Convert all XML entities

    @param text: a string containing entities possibly
    @type text: str
    @return: converted version of text
    @rtype: str
    '''
    return escape(text, {'"': '&quot;'}) if text else text


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
        line = (tcr.pk, tcr.case.pk,
                tcr.case.category.name.encode('utf-8'),
                tcr.case_run_status.name.encode('utf-8'),
                tcr.case.summary.encode('utf-8'),
                tcr.case.script.encode('utf-8'),
                tcr.case.is_automated,
                self.log_links(tcr),
                self.bug_ids(tcr))
        return line

    def log_links(self, tcr):
        '''
        Wrap log links into a single cell by
        joining log links.
        '''
        log_links = tcr.links.all()
        return ' '.join(
            [url.encode('utf-8')
             for url in tcr.links.values_list('url', flat=True)]
        )

    def bug_ids(self, tcr):
        '''
        Wrap bugs into a single cell by
        joining bug IDs.
        '''
        return ' '.join((
            str(pk) for pk in
            tcr.case.case_bug.values_list('bug_id', flat=True)
        ))

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

    def write_to_xml(self, output):
        write_to_output = output.write
        tcr_start_elem = u'<testcaserun case_run_id="%d" case_id="%d" ' \
                         u'category="%s" status="%s" summary="%s" ' \
                         u'scripts="%s" automated="%s">'

        write_to_output(u'<%s>' % self.root)
        for tcr in self.tcrs:
            summary = escape_entities(tcr.case.summary)
            script = escape_entities(tcr.case.script)
            write_to_output(tcr_start_elem % (tcr.pk, tcr.case.pk,
                                              tcr.case.category.name or u'',
                                              tcr.case_run_status.name,
                                              summary or u'',
                                              script or u'',
                                              str(tcr.case.is_automated)))
            write_to_output(u'<loglinks>')
            map(lambda link: write_to_output(u'<loglink name="%s" url="%s" />' %
                                             (link.name, link.url)),
                tcr.links.all())
            write_to_output(u'</loglinks>')
            write_to_output(u'<bugs>')
            map(lambda bug: write_to_output(u'<bug id="%d" />' % bug.bug_id),
                tcr.case_run_bug.all())
            write_to_output(u'</bugs>')
            write_to_output(u'</testcaserun>')
        write_to_output(u'</%s>' % self.root)
