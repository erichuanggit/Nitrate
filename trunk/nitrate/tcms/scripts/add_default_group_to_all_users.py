#!/usr/bin/env python
# @author: chaobin tang <ctang@redhat.com>
# Added on 18/05/2011

'''
A script that is supposed to run once
to add default groups defined in product_settings
to all existing users.
'''

from django.contrib.auth.models import User, Group
import tcms.product_settings as settings

def update():
    print "Starting to update user's group"
    users = User.objects.all()
    print "%s users to be updated" % users.count()
    default_groups = Group.objects.filter(name__in=settings.DEFAULT_GROUPS)
    print "%s groups to be added" % default_groups.count()
    for user in users:
        for grp in default_groups:
            user.groups.add(grp)
    raise SystemExit("Successfully Updated")

if __name__ == '__main__':
    update()
