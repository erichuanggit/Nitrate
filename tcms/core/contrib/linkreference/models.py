# -*- coding: utf-8 -*-

__all__ = ( 'create_link', 'LinkReference', )

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from tcms.core.models import TCMSContentTypeBaseModel

def create_link(name, url, link_to):
    '''Create new link reference and attach to the specific object

    The target object may be any model object.
    '''

    link = LinkReference(
        content_object=link_to, name=name, url=url, site_id=settings.SITE_ID)
    link.save()
    return link

class LinkReference(TCMSContentTypeBaseModel):

    name = models.CharField(max_length=64, blank=True, default='')
    url = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'tcms_linkrefs'
        index_together = (('content_type', 'object_pk', 'site'),)

    @classmethod
    def get_from(cls, target):
        ''' Retrieve all links attached to the target object already '''

        target_type = ContentType.objects.get_for_model(target)
        return cls.objects.filter(
            content_type__pk=target_type.id, object_pk=target.pk)

    @classmethod
    def unlink(cls, link_id):
        '''Remove the link

        If the link with link_id does not exist, unlink will keep quiet
        '''

        cls.objects.filter(id__in=[link_id,]).delete()
