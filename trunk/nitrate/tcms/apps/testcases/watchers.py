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

# Authors:
#   Xuqing Kuang <xkuang@redhat.com>, Chaobin Tang <ctang@redhat.com>

from tcms.apps.testcases.helpers import email
def on_case_save(sender, instance, created=False, **kwargs):
    # email changes
    if not created:
        if instance.emailing.notify_on_case_update:
            email.email_case_update(instance)

def on_case_delete(sender, instance, **kwargs):
    # email this deletion
    if instance.emailing.notify_on_case_delete:
        email.email_case_deletion(instance)
