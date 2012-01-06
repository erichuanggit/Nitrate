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

# FIXME: Use signal to handle log

import threading
import datetime

from tcms.plugins.message_bus.message_bus import MessageBus

# Reference from
# http://www.chrisdpratt.com/2008/02/16/signals-in-django-stuff-thats-not-documented-well/

class NewRunEmailThread(threading.Thread):
    def __init__(self, instance):
        self.instance = instance
        threading.Thread.__init__(self)
        
    def run(self):
        # The actual code we want to run
        self.instance.mail(
            template = 'mail/new_run.txt',
            subject = 'New run create from plan %s: %s' % (
                self.instance.plan_id, self.instance.summary
            ),
            context = { 'test_run': self.instance, }
        )

def post_run_saved(sender, *args, **kwargs):
    instance = kwargs['instance']
    if kwargs.get('created'):
        # Send the mail to default tester for alert him/her
        NewRunEmailThread(instance).start()
    else:
        # FIXME: Log, Plugin and other editing functions
        pass

# new testrun created info for qpid
def qpid_run_created(sender, *args, **kwargs):
    tr = kwargs['instance']
    if kwargs.get('created'):
        run_create_info = {
            "plan_id": tr.plan_id,
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "when": datetime.datetime.now().strftime("%Y-%m-%d %X")
        }    
        try:
            MessageBus().send(run_create_info, "testrun.created", False)
        except:
            pass

    else:
        # FIXME: Log, Plugin and other editing functions
        pass

# testrun progress/finish info for qpid
def qpid_run_progress(sender, *args, **kwargs):
    tcr = kwargs['instance']
    tr = tcr.run
    if not kwargs.get('created'):
        # testrun is progress
        run_info = {
            "plan_id": tr.plan_id,
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "when": datetime.datetime.now().strftime("%Y-%m-%d %X"),
        }

        if not tr.check_all_case_runs():
            # testrun is progress
            try:
                MessageBus().send(run_info, "testrun.progress", False)
            except:
                pass

        else:
            # testrun is finished 
            try:
                MessageBus().send(run_info, "testrun.finished", False)
            except:
                pass
    else:
        # FIXME: log, plugin and other editing functions
        pass
