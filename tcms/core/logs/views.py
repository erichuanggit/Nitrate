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
#   Chenxiong Qi <cqi@redhat.com>

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode

from models import TCMSLogModel


class TCMSLog(object):
    """TCMS Log"""

    def __init__(self, model):
        super(TCMSLog, self).__init__()
        self.model = model

    def get_new_log_object(self):
        elements = ['who', 'action']

        for element in elements:
            if not getattr(self, element): 
                raise NotImplementedError

        model = self.get_log_model()
        new = model(**self.get_log_create_data())

        return new

    def get_log_model(self):
        """
        Get the log model to create with this class.
        """
        return TCMSLogModel

    def get_log_create_data(self):
        return dict(
            content_object = self.model,
            who = self.who,
            action = self.action,
            site_id = settings.SITE_ID
        )

    def make(self, who, action):
        """Create new log"""
        self.who = who
        self.action = action

        model = self.get_new_log_object()
        model.save()

    def lookup_content_type(self):
        return ContentType.objects.get_for_model(self.model)

    def get_query_set(self):
        ctype = self.lookup_content_type()
        model = self.get_log_model()

        qs = model.objects.filter(content_type=ctype,
                                  object_pk=smart_unicode(self.model.pk),
                                  site=settings.SITE_ID)
        qs = qs.select_related('who')
        return qs

    def list(self):
        """List the logs"""
        return self.get_query_set().all()
