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
#   Xuqing Kuang <xkuang@redhat.com>, Chaobin Tang <ctang@redhat.com>

'''
Implementations of queries providing
both SQL-based query and full-text-based query.
'''

# from django
from django.db.models import Q
from django.db.models.query import QuerySet
from django.conf import settings
# from tcms
from testruns.models import TestRun
from testplans.models import TestPlan
from testcases.models import TestCase
# from stdlib
from types import FunctionType
from haystack.query import SearchQuerySet

CONTENT_TYPES = {
    'run': TestRun,
    'plan': TestPlan,
    'case': TestCase,
}

class SmartHaystackQuery(object):
    '''
    Class mainly wraps the look-up rules and priorities\n
    of fields that should be applied on haystack queryset.
    '''

    PRIORITIES = {
        'plan': (
            'pl_id', 'pl_summary', 'pl_authors', 'pl_product', 'pl_component',
            'pl_version', 'pl_type', 'pl_active', 'pl_created_since',
            'pl_created_before', 'pl_tags'),
        'case': (
            'cs_id', 'cs_summary', 'cs_authors', 'cs_tester', 'cs_tags', 'cs_bugs', 'cs_script',
            'cs_status', 'cs_auto', 'cs_proposed', 'cs_priority', 'cs_created_since',
            'cs_created_before', 'cs_product', 'cs_component', 'cs_category'),
        'run': (
            'r_id','r_summary', 'r_manager', 'r_tester', 'r_real_tester', 'r_running',
            'r_tags', 'r_created_since', 'r_created_before', 'r_product', 'r_build')
    }

    RULES = {
        'plan': {
            'pl_id': 'plan_id',
            'pl_summary': 'summary__startswith',
            'pl_type': 'plan_type__in',
            'pl_authors': 'author__in',
            'pl_tags': 'tags__in',
            'pl_active': 'is_active',
            'pl_created_since': 'create_date__gte',
            'pl_created_before': 'create_date__lte',
            'pl_product': 'product__in',
            'pl_component': 'component__in',
            'pl_version': 'version__in',
        },
        'case': {
            'cs_id': 'case_id__in',
            'cs_summary': 'summary__startswith',
            'cs_authors': 'author__in',
            'cs_tester': 'tester__in',
            'cs_tags': 'tags__in',
            'cs_bugs': 'bugs__in',
            'cs_status': 'status__in',
            'cs_auto': 'is_automated',
            'cs_proposed': 'is_auto_prop',
            'cs_priority': 'priority__in',
            'cs_script': 'script__startswith',
            'cs_created_since': 'create_date__gte',
            'cs_created_before': 'create_date__lte',
            'cs_component': 'components__in',
            'cs_category': 'category__in',
            'cs_product': 'product__in',
        },
        'run': {
            'r_id': 'run_id__in',
            'r_summary': 'summary__startswith',
            'r_manager': 'manager__in',
            'r_tester': 'tester__in',
            'r_running': 'is_finished',
            'r_tags': 'tags__in',
            'r_created_since': 'start_date__gte',
            'r_created_before': 'start_date__lte',
            'r_real_tester': 'real_tester__in',
            'r_product': 'product__in',
            'r_build': 'build__in',
            'r_version': 'version__in',
        }
    }

    ATTR_MAP = {
        'plan': {
            'plan': 'plan_id',
            'case': 'case_ids',
            'run': 'run_ids',
         },
        'case': {
            'plan': 'plan_ids',
            'case': 'case_id',
            'run': 'run_ids',
        },
        'run': {
            'plan': 'plan',
            'case': 'case_ids',
            'run': 'run_id'
        }
    }

    def __init__(self, queries, result_kls, target):
        self.queryset   = SearchQuerySet().models(CONTENT_TYPES[result_kls])
        self.queries    = queries
        self.result_kls = result_kls
        self.target     = target

    def filter(self):
        '''
        If values are all empty, return None.
        '''
        queryset = None
        rules = self.RULES[self.result_kls]
        for key in self.PRIORITIES[self.result_kls]:
            if not rules.has_key(key):
                continue
            value   = self.queries.get(key, None)
            # boolean type is a valid value, integer zero considered
            # invalid here.
            if isinstance(value, bool) or value:
                if settings.DEBUG:
                    print 'applying filter %s : %s' % (key, value)
                queryset = queryset or self.queryset
                if isinstance(value, QuerySet):
                    value = [v.pk for v in value]
                if self.queries.get(key+'_exclude', False):
                    queryset = queryset.exclude(**{rules[key]: value})
                else:
                    queryset = queryset.filter(**{rules[key]: value})
        self.queryset = queryset

    def evaluate(self):
        # call self.filter first to update the queryset
        self.filter()
        if self.queryset is None:
            yield None
        else:
            attr = self.ATTR_MAP[self.result_kls][self.target]
            for hit in self.queryset:
                val = getattr(hit, attr)
                if isinstance(val, list):
                    for key in val:
                        yield key
                else:
                    yield val

class SmartDjangoQuery(object):
    '''
    Class mainly wraps the look-up rules and priorities\n
    of fields that should be applied on Django queryset.\n
    Mind the priorities cause they make difference about efficiency.
    '''

    PRIORITIES = {
        'plan': (
            'pl_id', 'pl_authors', 'pl_product', 'pl_component',
            'pl_type', 'pl_version', 'pl_summary',
            'pl_active', 'pl_created_since', 'pl_created_before', 'pl_tags'),
        'case': (
            'cs_id', 'cs_authors', 'cs_tester', 'cs_product', 'cs_component', 'cs_tags',
            'cs_bugs', 'cs_proposed', 'cs_priority', 'cs_created_since', 'cs_status',
            'cs_auto', 'cs_created_before', 'cs_category', 'cs_summary', 'cs_script',),
        'run': (
            'r_id', 'r_product', 'r_manager', 'r_tester', 'r_real_tester',
            'r_assginee', 'r_build', 'r_version', 'r_running', 'r_tags',
            'r_created_since', 'r_created_before', 'r_summary',)
    }

    RULES = {
        'plan': {
            'pl_id': 'pk__in',
            'pl_summary': 'name__icontains',
            'pl_type': 'type_id__in',
            'pl_authors': 'author__username__in',
            'pl_tags': 'tag__name__in',
            'pl_active': 'is_active',
            'pl_created_since': 'create_date__gte',
            'pl_created_before': 'create_date__lte',
            'pl_product': 'product__id__in',
            'pl_component': 'component__in',
            'pl_version': 'version__in',
        },
        'case': {
            'cs_id': 'pk__in',
            'cs_summary': 'summary__icontains',
            'cs_authors': 'author__username__in',
            'cs_tester': 'default_tester__username__in',
            'cs_tags': 'tag__name__in',
            'cs_bugs': 'case_bug__bug_id__in',
            'cs_status': 'case_status__in',
            'cs_auto': 'is_automated',
            'cs_proposed': 'is_automated_proposed',
            'cs_priority': 'priority__in',
            'cs_script': 'script__icontains',
            'cs_created_since': 'create_date__gte',
            'cs_created_before': 'create_date__lte',
            'cs_component': 'component__in',
            'cs_category': 'category__in',
            'cs_product': lambda p: Q(category__product__in=p)|Q(component__product__in=p),
        },
        'run': {
            'r_id': 'pk__in',
            'r_summary': 'summary__icontains',
            'r_manager': 'manager__username__in',
            'r_assignee': 'case_run__assignee__username__in',
            'r_tester': 'default_tester__username__in',
            'r_running': 'stop_date__isnull',
            'r_tags': 'tag__name__in',
            'r_created_since': 'start_date__gte',
            'r_created_before': 'start_date__lte',
            'r_real_tester': 'case_run__tested_by__username__in',
            'r_product': 'build__product__in',
            'r_build': 'build__in',
            'r_version': 'product_version__in'
        }
    }

    def __init__(self, queries, result_kls, target):
        self.queryset   = CONTENT_TYPES[result_kls]._default_manager.all()
        self.queries    = queries
        self.result_kls = result_kls
        self.target     = target

    def filter(self):
        queryset = None
        rules    = self.RULES[self.result_kls]
        for key in self.PRIORITIES[self.result_kls]:
            if not rules.has_key(key):
                continue
            lookup  = rules[key]
            value   = self.queries.get(key, None)
            if isinstance(value, bool) or value:
                if settings.DEBUG:
                    print 'applying filter %s : %s' % (key, value)
                qs = queryset or self.queryset
                if self.queries.get(key+'_exclude', False):
                    # for complicated Q filtering
                    if isinstance(lookup, FunctionType):
                        queryset = qs.exclude(lookup(value))
                    else:
                        queryset = qs.exclude(**{lookup: value})
                else:
                    if isinstance(lookup, FunctionType):
                        queryset = qs.filter(lookup(value))
                    else:
                        queryset = qs.filter(**{lookup: value})
        self.queryset = queryset

    def evaluate(self):
        self.filter()
        return self.queryset or None
