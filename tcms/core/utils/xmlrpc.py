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

from datetime import datetime
from datetime import timedelta
from itertools import groupby

from django.db.models import ObjectDoesNotExist
from django.db.models.fields.related import ForeignKey, ManyToManyField

from tcms.core.forms.widgets import SECONDS_PER_DAY
from tcms.core.forms.widgets import SECONDS_PER_HOUR
from tcms.core.forms.widgets import SECONDS_PER_MIN


# TODO: to encode all strings in UTF-8 instead of mixing unicode and byte
#       string.
# TODO: to claim the sequence of the primary keys of each ManyToManyField is
#       arbitrary.


### Data format conversion functions ###

do_nothing = lambda value: value
to_str = lambda value: value if value is None else str(value)
encode_utf8 = lambda value: value if value is None else value.encode('utf-8')


def datetime_to_str(value):
    if value is None:
        return value
    return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")


def timedelta_to_str(value):
    if value is None:
        return value

    total_seconds = value.seconds + (value.days * SECONDS_PER_DAY)
    hours = total_seconds / SECONDS_PER_HOUR
    # minutes - Total seconds subtract the used hours
    minutes = total_seconds / SECONDS_PER_MIN - \
              total_seconds / SECONDS_PER_HOUR * 60
    seconds = total_seconds % SECONDS_PER_MIN
    return '%02i:%02i:%02i' % (hours, minutes, seconds)

### End of functions ###


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
            if isinstance(value, datetime):
                value = datetime_to_str(value)
            if isinstance(value, timedelta):
                value = timedelta_to_str(value)
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
        # From Python document 2.x:
        #   The returned group is itself an iterator that shares the underlying
        #   iterable with groupby(). Because the source is shared, when the
        #   groupby() object is advanced, the previous group is no longer
        #   visible. So, if that data is needed later, it should be stored as a
        #   list
        #
        # dict(groupby(qs.iterator(), lambda item: item['pk']))
        # will lose the group values and can not use dict comprehension in
        # Pyhton2.6
        return dict((pk, list(values)) for pk, values in groupby(qs.iterator(),
                                                                  lambda item: item['pk']))

    def _query_m2m_fields(self):
        m2m_fields = self._get_m2m_fields()
        result = [(field_name, self._query_m2m_field(field_name))
                  for field_name in m2m_fields]
        return dict(result)

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
        '''Core of QuerySet based serialization

        The process of serialization has following steps

        - Get data from database using QuerySet.values method
        - Transfer data to the output destiation according to serialization
          standard, where two things must be done,
          - field name must be replaced with right name rather than the internal
            name used for SQL query
          - some data must be converted in proper type. Currently, data with
            type datetime.datetime and datetime.timedelta must be converted to
            str (not UNICODE).
        - During the process of the above transfer, data associated with
          ManyToManyField should be retrieved from database and attached to each
          serialized data object.
        '''
        qs = self.queryset.values(*self._get_values_fields())
        primary_key_field = self._get_primary_key_field()
        values_fields_mapping = self._get_values_fields_mapping()
        m2m_fields = self._get_m2m_fields()
        m2m_not_queried = True
        serialize_result = []

        # Handle ManyToManyFields, add such fields' values to final
        # serialization
        for row in qs.iterator():
            # Replace name from ORM side to the serialization side as expected
            new_serialized_data = {}
            if values_fields_mapping:
                for orm_name, serialize_info in values_fields_mapping.iteritems():
                    serialize_name, conv_func = serialize_info
                    value = conv_func(row[orm_name])
                    new_serialized_data[serialize_name] = value
            else:
                # If no fields mapping, just use the original row as the
                # serialization result, and no data format conversion is
                # required obviously
                new_serialized_data.update(row)

            # Attach values of each ManyToManyField field
            # Lazy ManyToManyField query, to avoid query on ManyToManyFields if
            # serialization data is empty from database.
            if m2m_not_queried:
                m2m_fields_query = self._query_m2m_fields()
                m2m_not_queried = False
            model_pk = row[primary_key_field]
            for field_name in m2m_fields:
                related_object_pks = self._get_related_object_pks(m2m_fields_query,
                                                                  model_pk,
                                                                  field_name)
                new_serialized_data[field_name] = related_object_pks
            serialize_result.append(new_serialized_data)

        return serialize_result


class TestPlanXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''XMLRPC serializer specific for TestPlan'''

    values_fields_mapping = {
        'create_date': ('create_date', datetime_to_str),
        'default_product_version': ('default_product_version', do_nothing),
        'extra_link': ('extra_link', do_nothing),
        'is_active': ('is_active', do_nothing),
        'name': ('name', do_nothing),
        'plan_id': ('plan_id', do_nothing),

        'author': ('author_id', do_nothing),
        'author__username': ('author', to_str),
        'owner': ('owner_id', do_nothing),
        'owner__username': ('owner', to_str),
        'parent': ('parent_id', do_nothing),
        'parent__name': ('parent', encode_utf8),
        'product': ('product_id', do_nothing),
        'product__name': ('product', encode_utf8),
        'product_version': ('product_version_id', do_nothing),
        'product_version__value': ('product_version', encode_utf8),
        'type': ('type_id', do_nothing),
        'type__name': ('type', encode_utf8),
    }

    m2m_fields = ('attachment', 'case', 'component', 'env_group', 'tag')


class TestCaseRunXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''XMLRPC serializer specific for TestCaseRun'''

    values_fields_mapping = {
        'case_run_id': ('case_run_id', do_nothing),
        'case_text_version': ('case_text_version', do_nothing),
        'close_date': ('close_date', datetime_to_str),
        'environment_id': ('environment_id', do_nothing),
        'is_current': ('is_current', do_nothing),
        'notes': ('notes', do_nothing),
        'running_date': ('running_date', datetime_to_str),
        'sortkey': ('sortkey', do_nothing),

        'assignee': ('assignee_id', do_nothing),
        'assignee__username': ('assignee', to_str),
        'build': ('build_id', do_nothing),
        'build__name': ('build', encode_utf8),
        'case': ('case_id', do_nothing),
        'case__summary': ('case', encode_utf8),
        'case_run_status': ('case_run_status_id', do_nothing),
        'case_run_status__name': ('case_run_status', encode_utf8),
        'run': ('run_id', do_nothing),
        'run__summary': ('run', encode_utf8),
        'tested_by': ('tested_by_id', do_nothing),
        'tested_by__username': ('tested_by', to_str),
    }


class TestRunXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestRun'''

    values_fields_mapping = {
        'auto_update_run_status': ('auto_update_run_status', do_nothing),
        'environment_id': ('environment_id', do_nothing),
        'errata_id': ('errata_id', do_nothing),
        'estimated_time': ('estimated_time', str),
        'notes': ('notes', do_nothing),
        'plan_text_version': ('plan_text_version', do_nothing),
        'product_version': ('product_version', do_nothing),
        'run_id': ('run_id', do_nothing),
        'start_date': ('start_date', datetime_to_str),
        'stop_date': ('stop_date', datetime_to_str),
        'summary': ('summary', do_nothing),

        'build': ('build_id', do_nothing),
        'build__name': ('build', encode_utf8),
        'default_tester': ('default_tester_id', do_nothing),
        'default_tester__username': ('default_tester', to_str),
        'manager': ('manager_id', do_nothing),
        'manager__username': ('manager', to_str),
        'plan': ('plan_id', do_nothing),
        'plan__name': ('plan', encode_utf8),
    }


class TestCaseXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestCase'''

    values_fields_mapping = {
        'alias': ('alias', do_nothing),
        'arguments': ('arguments', do_nothing),
        'case_id': ('case_id', do_nothing),
        'create_date': ('create_date', datetime_to_str),
        'estimated_time': ('estimated_time', str),
        'extra_link': ('extra_link', do_nothing),
        'is_automated': ('is_automated', do_nothing),
        'is_automated_proposed': ('is_automated_proposed', do_nothing),
        'notes': ('notes', do_nothing),
        'requirement': ('requirement', do_nothing),
        'script': ('script', do_nothing),
        'summary': ('summary', do_nothing),

        'author': ('author_id', do_nothing),
        'author__username': ('author', to_str),
        'case_status': ('case_status_id', do_nothing),
        'case_status__name': ('case_status', encode_utf8),
        'category': ('category_id', do_nothing),
        'category__name': ('category', encode_utf8),
        'default_tester': ('default_tester_id', do_nothing),
        'default_tester__username': ('default_tester', to_str),
        'priority': ('priority_id', do_nothing),
        'priority__value': ('priority', encode_utf8),
        'reviewer': ('reviewer_id', do_nothing),
        'reviewer__username': ('reviewer', to_str),
        }


class ProductXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for Product'''

    values_fields_mapping = {
        'id': ('id', do_nothing),
        'name': ('name', do_nothing),
        'description': ('description', do_nothing),
        'milestone_url': ('milestone_url', do_nothing),
        'disallow_new': ('disallow_new', do_nothing),
        'vote_super_user': ('vote_super_user', do_nothing),
        'max_vote_super_bug': ('max_vote_super_bug', do_nothing),
        'votes_to_confirm': ('votes_to_confirm', do_nothing),
        'default_milestone': ('default_milestone', do_nothing),

        'classification': ('classification_id', do_nothing),
        'classification__name': ('classification', encode_utf8),
    }


class TestBuildXMLRPCSerializer(QuerySetBasedXMLRPCSerializer):
    '''Serializer for TestBuild'''

    values_fields_mapping = {
        'build_id': ('build_id', do_nothing),
        'description': ('description', do_nothing),
        'is_active': ('is_active', do_nothing),
        'milestone': ('milestone', do_nothing),
        'name': ('name', do_nothing),

        'product': ('product_id', do_nothing),
        'product__name': ('product', encode_utf8),
    }


if __name__ == '__main__':
    import xmlrpclib
    VERBOSE = 0
    server = xmlrpclib.ServerProxy('http://localhost:8080/xmlrpc/',
                                   verbose=VERBOSE)
    print server.TestRun.get_test_case_runs(137)
