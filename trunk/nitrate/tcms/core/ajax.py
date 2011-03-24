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
from django.contrib.auth.models import User

from tcms.testplans.models import TestPlan, TestCasePlan
from tcms.testcases.models import TestCase, TestCaseTag, TestCaseBugSystem as BugSystem
from tcms.testruns.models import TestRun, TestCaseRun, TestRunTag
from tcms.management.models import TestTag
from tcms.core.utils import get_string_combinations
from tcms.core.helpers.comments import add_comment

import datetime

def check_permission(request, ctype):
    perm = '%s.change_%s' % tuple(ctype.split('.'))
    if request.user.has_perm(perm):
        return True
    return False

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
            tp_pks = request.REQUEST.getlist('plan')
            tc_pks = request.REQUEST.getlist('case')
            tr_pks = request.REQUEST.getlist('run')
            if tp_pks:
                tags_set = TestTag.objects.filter(testplan__pk__in = tp_pks)
            if tc_pks:
                tags_set = TestTag.objects.filter(testcase__pk__in = tc_pks)
            elif tr_pks:
                tags_set = TestTag.objects.filter(testrun__pk__in = tr_pks)
            
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

def get_value_by_type(val, v_type):
    '''
    >>> get_value_by_type('True', 'bool')
    (1, None)
    >>> get_value_by_type('19860624 123059', 'datetime')
    (datetime.datetime(1986, 6, 24, 12, 30, 59), None)
    >>> get_value_by_type('5', 'int')
    ('5', None)
    >>> get_value_by_type('string', 'str')
    ('string', None)
    >>> get_value_by_type('everything', 'None')
    (None, None)
    >>> get_value_by_type('buggy', 'buggy')
    (None, 'Unsupported value type.')
    >>> get_value_by_type('string', 'int')
    (None, "invalid literal for int() with base 10: 'string'")
    '''
    value = error = None
    def get_time(time):
        DT = datetime.datetime
        if time == 'NOW': return DT.now()
        return DT.strptime(time, '%Y%m%d %H%M%S')
    pipes = {
        # Temporary solution is convert all of data to str
        # 'bool': lambda x: x == 'True',
        'bool': lambda x: x == 'True' and 1 or 0,
        'datetime': get_time,
        'int': lambda x: str(int(x)),
        'str': lambda x: str(x),
        'None': lambda x: None,
    }
    pipe = pipes.get(v_type, None)
    if pipe is None:
        error = 'Unsupported value type.'
    else:
        try: value = pipe(val)
        except Exception, e: error = str(e)
    return value, error

def say_no(error_msg):
    ajax_response = { 'rc': 1, 'response': error_msg}
    return HttpResponse(simplejson.dumps(ajax_response))

def say_yes():
    return HttpResponse(simplejson.dumps({'rc': 0, 'response': 'ok'}))

def update(request):
    '''
    Generic approach to update a model,\n
    based on contenttype.
    '''
    error = None
    now = datetime.datetime.now()

    data    = request.REQUEST.copy()
    ctype   = data.get("content_type")
    vtype   = data.get('value_type', 'str')
    object_pk = data.getlist("object_pk")
    field     = data.get('field')
    value     = data.get('value')

    if not field or not value or not object_pk or not ctype:
        return say_no('Following fields are required - content_type, object_pk, field and value.')

    # Convert the value type
    # FIXME: Django bug here: update() keywords must be strings
    field = str(field)

    value, error = get_value_by_type(value, vtype)
    if error: return say_no(error)
    has_perms = check_permission(request,ctype)
    if not has_perms: return say_no('Permission Dinied.')

    model = models.get_model(*ctype.split(".", 1))
    targets = model._default_manager.filter(pk__in=object_pk)

    if not targets: return say_no('No record found')
    if not hasattr(targets[0], field):
        return say_no('%s has no field %s' % (ctype, field))

    if hasattr(targets[0], 'log_action'):
        for t in targets:
            t.log_action(
                who = request.user,
                action = 'Field %s changed from %s to %s.' % (
                    field, getattr(t, field), value
                )
            )
    targets.update(**{field: value})

    if hasattr(model, 'mail_scene'):
        from tcms.core.utils.mailto import mailto
        mail_context = model.mail_scene(
            objects = targets, field = field, value = value, ctype = ctype, object_pk = object_pk,
        )
        if mail_context:
            mail_context['request'] = request
            try:
                mailto(**mail_context)
            except:
                pass

    # Special hacking for updating test case run status
    # https://bugzilla.redhat.com/show_bug.cgi?id=658160 
    if ctype == 'testruns.testcaserun' and field == 'case_run_status':
        if len(targets) == 1:
            targets[0].set_current()

        for t in targets:
            field = 'close_date'
            t.log_action(
                who = request.user,
                action = 'Field %s changed from %s to %s.' % (
                    field, getattr(t, field), now
                )
            )
            if t.tested_by != request.user:
                field = 'tested_by'
                t.log_action(
                    who = request.user,
                    action = 'Field %s changed from %s to %s.' % (
                        field, getattr(t, field), request.user
                    )
                )

            field = 'assignee'
            try:
                assignee = t.assginee
                if assignee != request.user:
                    t.log_action(
                        who = request.user,
                        action = 'Field %s changed from %s to %s.' % (
                            field, getattr(t, field), request.user
                        )
                    )
                    #t.assignee = request.user
                t.save()
            except:
                pass
        targets.update(close_date = now)
        targets.update(tested_by = request.user)
    return say_yes()

def comment_case_runs(request):
    '''
    Add comment to one or more caseruns at a time.
    '''
    data    = request.REQUEST.copy()
    comment = data.get('comment', None)
    if not comment: return say_no('Comments needed')
    run_ids = data.get('run', '').split(',')
    runs    = TestCaseRun.objects.filter(pk__in=run_ids)
    if not runs: return say_no('No caserun found.')
    add_comment(runs, comment, request.user)
    return say_yes()

def clean_bug_form(request):
    '''
    Verify the form data, return a tuple\n
    (None, ERROR_MSG) on failure\n
    or\n
    (data_dict, '') on success.\n
    '''
    data        = dict(request.REQUEST)
    bug_ids     = data.get('bugs', '')
    run_ids     = data.get('runs', '')
    bug_system  = data.get('bug_system')
    action      = data.get('action')
    try:
        data['bugs']    = map(int, bug_ids.split(','))
        data['runs']    = map(int, run_ids.split(','))
        bug_system      = int(bug_system)
    except (TypeError, ValueError), e:
        return (None, 'Please specify only integers for bugs, caseruns(using comma to seperate IDs),\
                and bug_system. (DEBUG INFO: %s)' % str(e))
    if action not in ('add', 'remove'):
        return (None, 'Actions only allow "add" and "remove".')
    try:
        data['bug_system'] = BugSystem.objects.get(pk=bug_system)
    except BugSystem.DoesNotExist:
        return (None, 'Specified bug system does not exist yet.')
    return (data, '')

def update_bugs_to_caseruns(request):
    '''
    Add one or more bugs to or remove that from\n
    one or more caserun at a time.
    '''
    data, error = clean_bug_form(request)
    if error: return say_no(error)
    runs    = TestCaseRun.objects.filter(pk__in=data['runs'])
    bg_sys  = data['bug_system']
    bugs    = data['bugs']
    action  = data['action']
    try:
        for run in runs:
            for bug in bugs:
                if action == 'add':
                    run.add_bug(bug_id=bug, bug_system=bg_sys)
                else:
                    run.remove_bug(bug)
    except Exception, e:
        return say_no(str(e))
    return say_yes()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
