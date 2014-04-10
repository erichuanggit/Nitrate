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

from django.contrib import admin

from kobo.django.xmlrpc.models import XmlRpcLog


class NitrateXmlRpcLogAdmin(admin.ModelAdmin):
    list_display = ('happened_on', 'user_username', 'method')
    list_per_page = 50
    list_filter = ('dt_inserted',)

    user_cache = {}

    def __init__(self, *args, **kwargs):
        NitrateXmlRpcLogAdmin.user_cache.clear()
        NitrateXmlRpcLogAdmin.user_cache = {}

        super(NitrateXmlRpcLogAdmin, self).__init__(*args, **kwargs)

    def user_username(self, obj):
        username = NitrateXmlRpcLogAdmin.user_cache.get(obj.user_id)
        if username is None:
            username = obj.user.username
            NitrateXmlRpcLogAdmin.user_cache[obj.user_id] = username
        return username
    user_username.short_description = 'username'

    def happened_on(self, obj):
        return obj.dt_inserted
    happened_on.short_description = 'Happened On'

admin.site.unregister(XmlRpcLog)
admin.site.register(XmlRpcLog, NitrateXmlRpcLogAdmin)
