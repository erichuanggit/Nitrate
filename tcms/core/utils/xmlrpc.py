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

import datetime

from itertools import groupby

from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models import ObjectDoesNotExist

from tcms.core.forms.widgets import SECONDS_PER_MIN, SECONDS_PER_HOUR, SECONDS_PER_DAY

class XMLRPCSerializer(object):
    """
    Django XMLRPC Serializer
    The goal is to process the datetime and timedelta data structure
    that python xmlrpclib can not handle.
    
    How to use it:
    # Model
    m = Model.objects.get(pk = 1)
    s = XMLRPCSerializer(model = m)
    s.serialize()
    
    Or
    # QuerySet
    q = Model.objects.all()
    s = XMLRPCSerializer(queryset = q)
    s.serialize()
    """
    def __init__(self, queryset=None, model=None):
        """Initial the class"""
        if hasattr(queryset, '__iter__'):
            self.queryset = queryset
            return
        elif hasattr(model, '__dict__'):
            self.model = model
            return
        
        raise TypeError("QuerySet(list) or Models(dictionary) is required")
   
   #FIXME: infinit loop here
   #def serialize(self):
   #     if hasattr(self, 'queryset'):
   #         return self.serialize_queryset()
   #         
   #     if hasattr(self, 'model'):
   #         return self.serialize_model()
    
    def serialize_model(self):
        """
        Check the fields of models and convert the data
        
        Returns: Dictionary
        """
        if not hasattr(self.model, '__dict__'):
            raise TypeError("Models or Dictionary is required")
        response = {}
        opts = self.model._meta
        for field in opts.local_fields:
            # for a django model, retrieving a foreignkey field
            # will fail when the field value isn't set
            try:
                value = getattr(self.model, field.name)
            except ObjectDoesNotExist:
                value = None
            if isinstance(value, datetime.datetime):
                value = datetime.datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
            if isinstance(value, datetime.timedelta):
                total_seconds = value.seconds + (value.days * SECONDS_PER_DAY)
                value = '%02i:%02i:%02i' % (
                    total_seconds / SECONDS_PER_HOUR, # hours
                    # minutes - Total seconds subtract the used hours
                    total_seconds / SECONDS_PER_MIN - total_seconds / SECONDS_PER_HOUR * 60,
                    total_seconds % SECONDS_PER_MIN # seconds
                )
            if isinstance(field, ForeignKey):
                fk_id = "%s_id" % field.name
                if value is None:
                    response[fk_id] = None
                else:
                    response[fk_id] = getattr(self.model, fk_id)
                    value = str(value)
            response[field.name] = value
        for field in opts.local_many_to_many:
            value = getattr(self.model, field.name)
            value = value.values_list('pk', flat=True)
            response[field.name] = list(value)
        return response

    def serialize_queryset(self):
        """
        Check the fields of QuerySet and convert the data

        Returns: List
        """
        response = []
        for m in self.queryset:
            self.model = m
            m = self.serialize_model()
            response.append(m)

        del self.queryset
        return response


class QuerySetBasedXMLRPCSerializer(XMLRPCSerializer):
    '''XMLRPC serializer specific for TestPlan

    To configure the serialization, developer can specify following class
    attribute, values_fields_mapping, m2m_fields, and primary_key.

    An unknown issue is that the primary key must appear in the
    values_fields_mapping. If doesn't, error would happen.
    '''

    # Define the mapping relationship of names from ORM side to XMLRPC output
    # side.
    # Key is the name from ORM side.
    # Value is the name from the the XMLRPC output side
    values_fields_mapping = {}

    def __init__(self, model_class, queryset):
        if model_class is None:
            raise ValueError('model_class should not be None')
        if queryset is None:
            raise ValueError('queryset should not be None')

        self.model_class = model_class
        self.queryset = queryset

    def _get_values_fields_mapping(self):
        return getattr(self.__class__, 'values_fields_mapping', {})

    def _get_values_fields(self):
        values_fields_mapping = self._get_values_fields_mapping()
        if values_fields_mapping:
            return values_fields_mapping.keys()
        else:
            return [field.name for field in self.model_class._meta.fields]

    def _get_m2m_fields(self):
        if hasattr(self.__class__, 'm2m_fields'):
            return self.__class__.m2m_fields
        else:
            return [field.name for field in
                    self.model_class._meta._many_to_many()]

    # TODO: how to deal with the situation that is primary key does not appear
    # in values fields, although such thing could not happen.
    def _get_primary_key_field(self):
        if hasattr(self.__class__, 'primary_key'):
            return self.__class__.primary_key
        else:
            fields = [field.name for field in self.model_class._meta.fields
                      if field.primary_key]
            if not fields:
                raise ValueError(
                    'Model %s has no primary key. You have to specify such '
                    'field manually.' % self.model_class.__name__)
            return fields[0]

    def _query_m2m_field(self, field_name):
        '''Query ManyToManyField order by model's pk

        Return value's format:
        {
            object_pk1: ({'pk': object_pk1, 'field_name': related_object_pk1},
                         {'pk': object_pk1, 'field_name': related_object_pk2},
                        ),
            object_pk2: ({'pk': object_pk2, 'field_name': related_object_pk3},
                         {'pk': object_pk2, 'field_name': related_object_pk4},
                         {'pk': object_pk3, 'field_name': related_object_pk5},
                        ),
            ...
        }

        @param field_name: field name of a ManyToManyField
        @type: field_name: str
        @return: dictionary mapping between model's pk and related object's pk
        @rtype: dict
        '''
        qs = self.queryset.values('pk', field_name).order_by('pk')
        result = {}
        for pk, values in groupby(qs.iterator(), lambda item: item['pk']):
            result[pk] = list(values)
        return result

    def _query_m2m_fields(self):
        m2m_fields = self._get_m2m_fields()
        return dict([(field_name, self._query_m2m_field(field_name))
                     for field_name in m2m_fields])

    def _get_single_field_related_object_pks(self,
                                             m2m_field_query,
                                             model_pk,
                                             field_name):
        return [item[field_name] for item in m2m_field_query[model_pk]
                if item[field_name]]

    def _get_related_object_pks(self, m2m_fields_query, model_pk, field_name):
        data = m2m_fields_query[field_name]
        return self._get_single_field_related_object_pks(data,
                                                         model_pk,
                                                         field_name)

    def serialize_queryset(self):
        qs = self.queryset.values(*self._get_values_fields())
        m2m_fields_query = self._query_m2m_fields()
        primary_key_field = self._get_primary_key_field()
        values_fields_mapping = self._get_values_fields_mapping()
        serialize_result = []

        # Handle ManyToManyFields, add such fields' values to final
        # serialization
        for row in qs:
            # Replace name from ORM side to the serialization side as expected
            new_serialized_data = {}
            if values_fields_mapping:
                for orm_name, serialize_name in values_fields_mapping.iteritems():
                    new_serialized_data[serialize_name] = row[orm_name]
            else:
                new_serialized_data.update(row)

            # Attach values of each ManyToManyField field
            model_pk = row[primary_key_field]
            for field_name in self._get_m2m_fields():
                related_object_pks = self._get_related_object_pks(m2m_fields_query,
                                                                  model_pk,
                                                                  field_name)
                new_serialized_data[field_name] = related_object_pks
            serialize_result.append(new_serialized_data)

        return serialize_result


class TestPlanXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''XMLRPC serializer specific for TestPlan'''

    values_fields_mapping = {
        'plan_id': 'plan_id',
        'default_product_version': 'default_product_version',
        'name': 'name',
        'create_date': 'create_date',
        'is_active': 'is_active',
        'extra_link': 'extra_link',
        'product_version': 'product_version_id',
        'product_version__value': 'product_verison',
        'owner': 'owner_id',
        'owner__username': 'owner',
        'author': 'author_id',
        'author__username': 'author',
        'product': 'product_id',
        'product__name': 'product',
        'type': 'type_id',
        'type__name': 'type',
        'parent': 'parent_id',
        'parent__name': 'parent',
    }

    m2m_fields = ('attachment', 'case', 'component', 'env_group', 'tag')


class TestCaseRunXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''XMLRPC serializer specific for TestCaseRun'''

    values_fields_mapping = {
        'is_current': 'is_current',
        'case_run_id': 'case_run_id',
        'running_date': 'running_date',
        'close_date': 'close_data',
        'case_text_version': 'case_text_version',
        'sortkey': 'sortkey',
        'environment_id': 'environment_id',
        'notes': 'notes',

        'assignee': 'assignee_id',
        'assignee__username': 'assignee',
        'tested_by': 'tested_by_id',
        'tested_by__username': 'tested_by',
        'run': 'run_id',
        'run__summary': 'run',
        'case': 'case_id',
        'case__summary': 'case',
        'case_run_status': 'case_run_status__id',
        'case_run_status__name': 'case_run_status',
        'build': 'build_id',
        'build__name': 'build',
    }

    def _get_m2m_fields(self):
        '''
        Do not handle GenericRelation field due to this field wasn't handled
        '''
        return []


class TestRunXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestRun'''

    values_fields_mapping = {
        'auto_update_run_status': 'auto_update_run_status',
        'product_version': 'product_version',
        'run_id': 'run_id',
        'start_date': 'start_date',
        'stop_date': 'stop_date',
        'errata_id': 'errata_id',
        'plan_text_version': 'plan_text_version',
        'environment_id': 'environment_id',
        'summary': 'summary',
        'notes': 'notes',

        'plan': 'plan_id',
        'plan__name': 'plan',
        'build': 'build_id',
        'build__name': 'build',
        'manager': 'manager_id',
        'manager__username': 'manager',
        'default_tester': 'default_tester_id',
        'default_tester__username': 'default_tester',
        'estimated_time': 'estimated_time',
        }


class TestCaseXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestCase'''

    values_fields_mapping = {
        'is_automated_proposed': 'is_automated_proposed',
        'extra_link': 'extra_link',
        'summary': 'summary',
        'requirement': 'requirement',
        'alias': 'alias',
        'case_id': 'case_id',
        'create_date': 'create_date',
        'is_automated': 'is_automated',
        'script': 'script',
        'arguments': 'arguments',
        'notes': 'notes',

        'case_status': 'case_status_id',
        'case_status__name': 'case_status',
        'category': 'category_id',
        'category__name': 'category',
        'priority': 'priority_id',
        'priority__value': 'priority',
        'author': 'author_id',
        'author__username': 'author',
        'default_tester': 'default_tester_id',
        'default_tester__username': 'default_tester',
        'reviewer': 'reviewer_id',
        'reviewer__username': 'reviewer',
        'estimated_time': 'estimated_time',
        }


class ProductXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for Product'''

    values_fields_mapping = {
        'id': 'id',
        'name': 'name',
        'description': 'description',
        'milestone_url': 'milestone_url',
        'disallow_new': 'disallow_new',
        'vote_super_user': 'vote_super_user',
        'max_vote_super_bug': 'max_vote_super_bug',
        'votes_to_confirm': 'votes_to_confirm',
        'default_milestone': 'default_milestone',

        'classification': 'classification_id',
        'classification__name': 'classification',
        }


class TestBuildXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestBuild'''

    values_fields_mapping = {
        'build_id': 'build_id',
        'name': 'name',
        'milestone': 'milestone',
        'description': 'description',
        'is_active': 'is_active',
        'product': 'product_id',
        'product__name': 'product',
    }


if __name__ == '__main__':
    import xmlrpclib
    VERBOSE = 0
    server = xmlrpclib.ServerProxy('http://localhost:8080/xmlrpc/',
                                   verbose=VERBOSE)
    print server.TestRun.get_test_case_runs(137)
