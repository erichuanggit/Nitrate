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

import threading
import datetime

from tcms.integration.djqpid import Producer

# Reference from
# http://www.chrisdpratt.com/2008/02/16/signals-in-django-stuff-thats-not-documented-well/

# FIXME: Used in views so far, may be reimplement by signal in future.
class EditCaseNotifyThread(threading.Thread):
    def __init__(self, instance, cleaned_data, request, to):
        self.instance = instance
        self.cleaned_data = cleaned_data
        self.request = request
        self.to = to
        threading.Thread.__init__(self)
    
    def run(self):
        # The actual code we want to run
        txt = self.instance.latest_text()
        self.instance.mail(
            template = 'mail/edit_case.txt',
            subject = 'Case %s - %s has been edited by: %s' % (
                self.instance.pk, self.instance.summary, self.request.user,
            ),
            context = {
                'test_case': self.instance, 'test_case_text': txt,
                'test_case_plain_text': txt.get_plain_text(),
                'cleaned_data': self.cleaned_data
            },
            to = self.to,
            request = self.request,
        )

# Bug add listen for qpid
def bug_add_listen(sender, *args, **kwargs):
    tcr_bug = kwargs['instance']
    if tcr_bug.case_run:
        #signal is raise by testcaserun
        tr = tcr_bug.case_run.run
    else:
        #signal is raise by testcase
        return
    if tr.errata_id:
        qpid_bug_add = {
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "bug_id": tcr_bug.bug_id,
            "when": datetime.datetime.now().strftime("%Y-%m-%d %X"),
        }
        # qpid message send
        try:
            Producer().send(qpid_bug_add, "bugs.added", False)
        except:
            pass
    else:
        # FIXME
        pass

# Bug remove listen for qpid
def bug_remove_listen(sender, *args, **kwargs):
    tcr_bug = kwargs['instance']
    if tcr_bug.case_run:
        #signal is raise by testcaserun
        tr = tcr_bug.case_run.run
    else:
        #signal is raise by testcase
        return
    if tr.errata_id:
        qpid_bug_remove = {
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "bug_id": tcr_bug.bug_id,
            "when": datetime.datetime.now().strftime("%Y-%m-%d %X"),
        }
        # qpid message send
        try:
            Producer().send(qpid_bug_remove, "bugs.dropped", False)
        except:
            pass
    else:
        # FIXME
        pass
        

   
