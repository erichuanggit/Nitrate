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

"""
Shared functions for plan/case/run.

Most of these functions are use for Ajax.
"""
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.utils import simplejson
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import user_passes_test

from tcms.testplans.models import TestPlan, TestCasePlan
from tcms.testcases.models import TestCase, TestCaseTag
from tcms.testruns.models import TestRun, TestCaseRun, TestRunTag
from tcms.management.models import TestTag

from tcms.core.utils import get_string_combinations

def check_permission(request, perm, response = {}):
    """Shared function for check permission"""
    if request.user.has_perm(perm):
        return True
    
    response['rc'] = 1
    response['response'] = 'Permission denied'
    return response

def strip_parameters(request, skip_parameters):
    parameters = {}
    for dict_ in request.REQUEST.dicts:
        for k, v in dict_.items():
            if k not in skip_parameters and v:
                parameters[str(k)] = v
    
    return parameters

def info(request):
    """Ajax responsor for misc information"""
    from django.core import serializers
    
    class Objects(object):
        __all__ = [
            'builds', 'categories', 'components', 'envs', 'env_groups',
            'env_properties', 'env_values', 'tags', 'users', 'versions'
        ]
        
        def __init__(self, request, product_id = None):
            self.request = request
            self.product_id = product_id
            self.internal_parameters = ('info_type', 'field', 'format')
        
        def builds(self):
            from tcms.management.models import TestBuild
            query = {
                'product_id': self.product_id,
                'is_active': self.request.REQUEST.get('is_active')
            }
            return TestBuild.list(query)
        
        def categories(self):
            from tcms.testcases.models import TestCaseCategory
            return TestCaseCategory.objects.filter(product__id = self.product_id)
        
        def components(self):
            from tcms.management.models import Component
            return Component.objects.filter(product__id = self.product_id)
        
        def envs(self):
            from tcms.management.models import TestEnvironment
            return TestEnvironment.objects.filter(product__id = self.product_id)
        
        def env_groups(self):
            from tcms.management.models import TCMSEnvGroup
            return TCMSEnvGroup.objects.all()
        
        def env_properties(self):
            from tcms.management.models import TCMSEnvGroup, TCMSEnvProperty
            if self.request.REQUEST.get('env_group_id'):
                env_group = TCMSEnvGroup.objects.get(
                    id = self.request.REQUEST['env_group_id']
                )
                return env_group.property.all()
            else:
                return TCMSEnvProperty.objects.all()
        
        def env_values(self):
            from tcms.management.models import TCMSEnvValue
            return TCMSEnvValue.objects.filter(
                property__id = self.request.REQUEST.get('env_property_id')
            )
        
        def tags(self):
            query = strip_parameters(request, self.internal_parameters)
            tags = TestTag.objects
            # Generate the string combination, because we are using
            # case sensitive table
            if query.get('name__startswith'):
                seq = get_string_combinations(query['name__startswith'])
                tags = tags.filter(eval(
                    '|'.join(["Q(name__startswith = '%s')" % item for item in seq])
                ))
                del query['name__startswith']
            
            tags = tags.filter(**query).distinct()
            return tags
        
        def users(self):
            from django.contrib.auth.models import User
            query = strip_parameters(self.request, self.internal_parameters)
            return User.objects.filter(**query)
        
        def versions(self):
            from tcms.management.models import Version
            return Version.objects.filter(product__id = self.product_id)
        
    objects = Objects(request = request, product_id = request.REQUEST.get('product_id'))
    obj = getattr(objects, request.REQUEST.get('info_type'), None)
    
    if obj:
        if request.REQUEST.get('format') == 'ulli':
            field = request.REQUEST.get('field', 'name')
            response_str = '<ul>'
            for o in obj():
                response_str += '<li>' + getattr(o, field, None) + '</li>'
            response_str += '</ul>'
            return HttpResponse(response_str)
        
        return HttpResponse(serializers.serialize(
            request.REQUEST.get('format', 'json'),
            obj(),
            excludes=('password',)
        ))
    
    return HttpResponse('Unrecognizable infotype')

def form(request):
    """Response get form ajax call, most using in dialog"""
    import tcms

    # The parameters in internal_parameters will delete from parameters
    internal_parameters = ['app_form', 'format']
    parameters = strip_parameters(request, internal_parameters)
    q_app_form = request.REQUEST.get('app_form')
    q_format = request.REQUEST.get('format')
    if not q_format:
        q_format = 'p'
    
    if not q_app_form:
        return HttpResponse('Unrecognizable app_form')
    
    # Get the form
    q_app, q_form = q_app_form.split('.')[0], q_app_form.split('.')[1]
    exec('from tcms.%s.forms import %s as form' % (q_app, q_form))
    form = form(initial=parameters)
    
    # Generate the HTML and reponse
    html = getattr(form, 'as_' + q_format)
    return HttpResponse(html())

def tag(request, template_name="management/get_tag.html"):
    """Get tags for test plan or test case"""
    from django.utils import simplejson
    from django.core import serializers
    from tcms.management.models import TestTag
    
    class Objects(object):
        __all__ = ['plan', 'case', 'run']
        
        def __init__(self, request, template_name):
            self.template_name = template_name
            for o in self.__all__:
                if request.REQUEST.get(o):
                    self.object = o
                    self.object_pks = request.REQUEST.getlist(o)
                    break
        
        def get(self):
            func = getattr(self, self.object)
            return func()
        
        def plan(self):
            return self.template_name, TestPlan.objects.filter(pk__in = self.object_pks)
        
        def case(self):
            return self.template_name, TestCase.objects.filter(pk__in = self.object_pks)
        
        def run(self):
            self.template_name = 'run/get_tag.html'
            return self.template_name, TestRun.objects.filter(pk__in = self.object_pks)
    
    class TagActions(object):
        __all__ = ['add', 'remove']
        
        def __init__(self, obj, tag):
            self.obj = obj
            self.tag = TestTag.string_to_list(tag)
            self.request = request
            
        def add(self):
            for tag_str in self.tag:
                try:
                    tag, c = TestTag.objects.get_or_create(name = tag_str)
                    for o in self.obj:
                        o.add_tag(tag)
                except:
                    return "Error when adding %s" % self.tag

            return True
        
        def remove(self):
            tp_case_ids = request.REQUEST.getlist('case')
            tp_run_ids = request.REQUEST.getlist('run')
            if tp_case_ids:
                tag_ids = TestCaseTag.objects.filter(case__in = tp_case_ids).distinct().values_list('tag')
            elif tp_run_ids:
                tag_ids = TestRunTag.objects.filter(run__in = tp_run_ids).distinct().values_list('tag')

            tags_set = TestTag.objects.filter(id__in = tag_ids)

            for tag_str in self.tag:
                try:
                    tag = tags_set.filter(name = tag_str)[0]
                except IndexError:
                    return "Tag %s does not exist in current plan." % tag_str
                
                for o in self.obj:
                    try:
                        o.remove_tag(tag)
                    except:
                        return "Remove tag %s error." % tag
            return True
    
    objects = Objects(request, template_name)
    template_name, obj = objects.get()
    
    q_tag = request.REQUEST.get('tags')
    q_action = request.REQUEST.get('a')
    if q_action:
        tag_actions = TagActions(obj = obj, tag = q_tag)
        func = getattr(tag_actions, q_action)
        response = func()
        if response != True:
            return HttpResponse(simplejson.dumps({'response': response, 'rc': 1}))
    
    del q_tag, q_action
    
    # Response to batch operations
    if request.REQUEST.get('t') == 'json':
        if request.REQUEST.get('f') == 'serialized':
            return HttpResponse(
                serializers.serialize(request.REQUEST['t'], obj)
            )
        
        return HttpResponse(simplejson.dumps({'response': 'ok'}))
    
    # Response the single operation
    if len(obj) == 1:
        tags = obj[0].tag.all()
        
        tags = tags.extra(select={
            'num_plans': 'SELECT COUNT(*) FROM test_plan_tags WHERE test_tags.tag_id = test_plan_tags.tag_id',
            'num_cases': 'SELECT COUNT(*) FROM test_case_tags WHERE test_tags.tag_id = test_case_tags.tag_id',
            'num_runs': 'SELECT COUNT(*) FROM test_run_tags WHERE test_tags.tag_id = test_run_tags.tag_id',
        })
        
        return direct_to_template(request, template_name, {
            'tags': tags,
            'object': obj[0],
        })
    
    return HttpResponse('')

def update(request):
    """Modify the object attributes"""
    import datetime
    from django.utils import simplejson
    # Initial the response
    ajax_response = { 'rc': 0, 'response': 'ok' }
    
    # Initial the data
    data = request.REQUEST.copy()
    ctype = data.get("content_type")
    vtype = data.get('value_type', 'str')
    object_pk = data.getlist("object_pk")
    field = data.get('field')
    value = data.get('value')
    
    if not field or not value or not object_pk or not ctype:
        ajax_response['rc'] = 1
        ajax_response['response'] = 'Following fields are required - content_type, object_pk, field and value.'
        return HttpResponse(simplejson.dumps(ajax_response))
    
    # Convert the value type
    # FIXME: Django bug here: update() keywords must be strings
    field = str(field)
    value_types = {
        # Temporary solution is convert all of data to str
        # 'bool': lambda x: x == 'True',
        'bool': lambda x: x == 'True' and 1 or 0,
        'datetime': lambda x: x == 'NOW' and str(datetime.datetime.now()) or str(datetime.datetime(x)), # FIXME
        'int': lambda x: str(int(x)),
        'str': lambda x: str(x),
        'None': lambda x: None,
    }
    try:
        value = value_types.get(vtype)(value)
    except TypeError, error:
        ajax_response['rc'] = 1
        ajax_response['response'] = 'Value type caused to error - '  + error
        return HttpResponse(simplejson.dumps(ajax_response))
    
    # Check permission
    no_perms = check_permission(
        request = request,
        perm = '%s.change_%s' % tuple(ctype.split('.')),
        response = ajax_response,
    )
    
    if not isinstance(no_perms, bool) and bool:
        return HttpResponse(simplejson.dumps(no_perms))
    
    # Get object
    try:
        model = models.get_model(*ctype.split(".", 1))
        targets = model._default_manager.filter(pk__in = object_pk)
    except:
        raise
    
    if not targets:
        ajax_response['rc'] = 1
        ajax_response['response'] = 'You specific content(s) is not exist in database.'
        return HttpResponse(simplejson.dumps(ajax_response))
    
    if not hasattr(targets[0], field):
        ajax_response['rc'] = 1
        ajax_response['response'] = 'Not field %s for context_type %s' % (
            field, ctype
        )
        return HttpResponse(simplejson.dumps(ajax_response))
    
    if hasattr(targets[0], 'log_action'):
        try:
            for t in targets:
                t.log_action(
                    who = request.user,
                    action = 'Field %s changed from %s to %s.' % (
                        field, getattr(t, field), value
                    )
                )
        except:
            raise
    from pprint import pprint
    pprint({field: value})
    targets.update(**{field: value})
    
    if hasattr(targets[0], 'mail_scene'):
        t = targets[0]
        t.mail_scene(
            objects = targets, field = field, value = value, ctype = ctype,
            object_pk = object_pk, request = request
        )
    
    del ctype, object_pk, field, value, targets
    return HttpResponse(simplejson.dumps(ajax_response))
