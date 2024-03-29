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

from django.contrib.contenttypes.models import ContentType
from django.db import models

from tcms.core.models import TCMSContentTypeBaseModel

from managers import TCMSLogManager

# Create your models here.

class TCMSLogModel(TCMSContentTypeBaseModel):
    who = models.ForeignKey('auth.User', related_name='log_who')
    date = models.DateTimeField(auto_now_add=True)
    action = models.TextField()

    objects = TCMSLogManager()

    class Meta:
        abstract = False
        db_table = u'tcms_logs'
        index_together = (('content_type', 'object_pk', 'site'),)

    def __unicode__(self):
        return self.action

    @classmethod
    def get_logs_for_model(cls, model_class, object_pk):
        ct = ContentType.objects.get_for_model(model_class)
        return cls.objects.filter(content_type=ct, object_pk=object_pk)
