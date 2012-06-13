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

from kobo.django.xmlrpc.decorators import user_passes_test, login_required, log_call
from tcms.apps.testplans.models import TestPlan, TestPlanType
from tcms.apps.management.models import TestTag
from utils import pre_process_ids

__all__ = (
    'add_tag',
    'check_plan_type',
    'create',
    'filter',
    'filter_count',
    'get',
    'get_change_history',
    'get_env_groups',
    'get_plan_type',
    'get_product',
    'get_tags',
    'get_test_cases',
    'get_all_cases_tags',
    'get_test_runs',
    'get_text',
    'lookup_type_id_by_name',
    'lookup_type_name_by_id',
    'remove_tag',
    'store_text',
    'update',
)

@log_call
@user_passes_test(lambda u: u.has_perm('testplans.add_testplantag'))
def add_tag(request, plan_ids, tags):
    """
    Description: Add one or more tags to the selected test plans.

    Params:      $plan_ids - Integer/Array/String: An integer representing the ID of the plan in the database,
                      an arry of plan_ids, or a string of comma separated plan_ids.

                  $tags - String/Array - A single tag, an array of tags,
                      or a comma separated list of tags.

    Returns:     Array: empty on success or an array of hashes with failure
                  codes if a failure occured.

    Example:
    # Add tag 'foobar' to plan 1234
    >>> TestPlan.add_tag(1234, 'foobar')
    # Add tag list ['foo', 'bar'] to plan list [12345, 67890]
    >>> TestPlan.add_tag([12345, 67890], ['foo', 'bar'])
    # Add tag list ['foo', 'bar'] to plan list [12345, 67890] with String
    >>> TestPlan.add_tag('12345, 67890', 'foo, bar')
    """
    from tcms.apps.management.models import TestTag
    tps = TestPlan.objects.filter(
        plan_id__in = pre_process_ids(value = plan_ids)
    )
    tags = TestTag.string_to_list(tags)

    for tag in tags:
        t, c = TestTag.objects.get_or_create(name = tag)
        for tp in tps:
            tp.add_tag(tag = t)

    return

def check_plan_type(request, name):
    """
    Params:      $name - String: the plan type.

    Returns:     Hash: Matching plan type object hash or error if not found.

    Example:
    >>> TestPlan.check_plan_type('regression')
    """
    return TestPlanType.objects.get(name = name).serialize()

@log_call
@user_passes_test(lambda u: u.has_perm('testplans.add_testplan'))
def create(request, values):
    """
    Description: Creates a new Test Plan object and stores it in the database.

    Params:      $values - Hash: A reference to a hash with keys and values
                  matching the fields of the test plan to be created.
      +-------------------------+----------------+-----------+------------------------------------+
      | Field                   | Type           | Null      | Description                        |
      +-------------------------+----------------+-----------+------------------------------------+
      | product                 | Integer        | Required  | ID of product                      |
      | name                    | String         | Required  |                                    |
      | type                    | Integer        | Required  | ID of plan type                    |
      | default_product_version | Integer        | Required  |                                    |
      | text                    | String         | Required  | Plan documents, HTML acceptable.   |
      | parent                  | Integer        | Optional  | Parent plan ID                     |
      | is_active               | Boolean        | Optional  | 0: Archived 1: Active (Default 0)  |
      +-------------------------+----------------+-----------+------------------------------------+

    Returns:     The newly created object hash.

    Example:
    # Minimal test case parameters
    >>> values = {
        'product': 61,
        'name': 'Testplan foobar',
        'type': 1,
        'parent_id': 150,
        'default_product_version': 93,
        'text':'Testing TCMS',
    }
    >>> TestPlan.create(values)
    """
    from tcms.core import forms
    from tcms.apps.testplans.forms import XMLRPCNewPlanForm

    if not values.get('product'):
        raise ValueError('Value of product is required')

    form = XMLRPCNewPlanForm(values)
    form.populate(product_id = values['product'])

    if form.is_valid():
        tp = TestPlan.objects.create(
            product = form.cleaned_data['product'],
            name = form.cleaned_data['name'],
            type = form.cleaned_data['type'],
            author = request.user,
            default_product_version = form.cleaned_data['default_product_version'],
            parent = form.cleaned_data['parent'],
            is_active = form.cleaned_data['is_active']
        )

        tp.add_text(
            author = request.user,
            plan_text = values['text'],
        )

        return tp.serialize()
    else:
        return forms.errors_to_list(form)

def filter(request, values = {}):
    """
    Description: Performs a search and returns the resulting list of test plans.

    Params:      $values - Hash: keys must match valid search fields.

        +------------------------------------------------------------+
        |                   Plan Search Parameters                   |
        +----------------------------------------------------------+
        |        Key              |          Valid Values            |
        | author                  | ForeignKey: Auth.User            |
        | attachment              | ForeignKey: Attachment           |
        | case                    | ForeignKey: Test Case            |
        | create_date             | DateTime                         |
        | default_product_version | String                           |
        | env_group               | ForeignKey: Environment Group    |
        | name                    | String                           |
        | plan_id                 | Integer                          |
        | product                 | ForeignKey: Product              |
        | tag                     | ForeignKey: Tag                  |
        | text                    | ForeignKey: Test Plan Text       |
        | type                    | ForeignKey: Test Plan Type       |
        +------------------------------------------------------------+

    Returns:     Array: Matching test plans are retuned in a list of plan object hashes.

    Example:
    # Get all of plans contain 'TCMS' in name
    >>> TestPlan.filter({'name__icontain': 'TCMS'})
    # Get all of plans create by xkuang
    >>> TestPlan.filter({'author__username': 'xkuang'})
    # Get all of plans the author name starts with x
    >>> TestPlan.filter({'author__username__startswith': 'x'})
    # Get plans contain the case ID 12345, 23456, 34567
    >>> TestPlan.filter({'case__case_id__in': [12345, 23456, 34567]})
    """
    return TestPlan.to_xmlrpc(values)

def filter_count(request, values = {}):
    """
    Description: Performs a search and returns the resulting count of plans.

    Params:      $values - Hash: keys must match valid search fields (see filter).

    Returns:     Integer - total matching plans.

    Example:
    # See TestPlan.filter()
    """
    return TestPlan.objects.filter(**values).count()

def get(request, plan_id):
    """
    Description: Used to load an existing test plan from the database.

    Params:      $id - Integer/String: An integer representing the ID of this plan in the database

    Returns:     Hash: A blessed TestPlan object hash

    Example:
    >>> TestPlan.get(137)
    """
    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except TestPlan.DoesNotExist, error:
        return error
    response = tp.serialize()
    #get the xmlrpc tags
    tag_ids = tp.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    tags = TestTag.to_xmlrpc(query)
    #cut 'id' attribute off, only leave 'name' here
    tags_without_id = map(lambda x:x["name"], tags)
    #replace tag_id list in the serialize return data
    response["tag"] = tags_without_id
    return response

def get_change_history(request, plan_id):
    """
    *** FIXME: NOT IMPLEMENTED - History is different than before ***
    Description: Get the list of changes to the fields of this plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

    Returns:     Array: An array of hashes with changed fields and their details.
    """
    pass

def get_env_groups(request, plan_id):
    """
    Description: Get the list of env groups to the fields of this plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

    Returns:     Array: An array of hashes with env groups.
    """
    from tcms.apps.management.models import TCMSEnvGroup

    query = {'testplan__pk': plan_id}
    return TCMSEnvGroup.to_xmlrpc(query)

def get_plan_type(request, id):
    """
    Params:      $id - Integer: ID of the plan type to return

    Returns:     Hash: Matching plan type object hash or error if not found.

    Example:
    >>> TestPlan.get_plan_type(3)
    """
    return TestPlanType.objects.get(id = id).serialize()

def get_product(request, plan_id):
    """
    Description: Get the Product the plan is assiciated with.

    Params:      $plan_id - Integer: An integer representing the ID of the plan in the database.

    Returns:     Hash: A blessed Product hash.

    Example:
    >>> TestPlan.get_product(137)
    """
    return TestPlan.objects.select_related('product').get(pk = plan_id).product.serialize()

def get_tags(request, plan_id):
    """
    Description: Get the list of tags attached to this plan.

    Params:      $plan_id - Integer An integer representing the ID of this plan in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestPlan.get_tags(137)
    """
    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except:
        raise

    tag_ids = tp.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)

def get_all_cases_tags(request, plan_id):
    """
    Description: Get the list of tags attached to this plan's testcases.

    Params:      $plan_id - Integer An integer representing the ID of this plan in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestPlan.get_all_cases_tags(137)
    """
    from tcms.apps.management.models import TestTag
    try:
        tp = TestPlan.objects.get(plan_id = plan_id)
    except:
        raise

    tcs = tp.case.all()
    tag_ids=[]
    for tc in tcs:
        tag_ids.extend(tc.tag.values_list('id', flat=True))
    tag_ids=list(set(tag_ids))
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)

def get_test_cases(request, plan_id):
    """
    Description: Get the list of cases that this plan is linked to.

    Params:      $plan_id - Integer: An integer representing the ID of the plan in the database

    Returns:     Array: An array of test case object hashes.

    Example:
    >>> TestPlan.get_test_cases(137)
    """
    from tcms.apps.testcases.models import TestCase
    query = {'plan': plan_id}
    return TestCase.to_xmlrpc(query)

def get_test_runs(request, plan_id):
    """
    Description: Get the list of runs in this plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

    Returns:     Array: An array of test run object hashes.

    Example:
    >>> TestPlan.get_test_runs(plan_id)
    """
    from tcms.apps.testruns.models import TestRun
    query = {'plan': plan_id}
    return TestRun.to_xmlrpc(query)

def get_text(request, plan_id, plan_text_version = None):
    """
    Description: The plan document for a given test plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

                 $version - Integer: (OPTIONAL) The version of the text you want returned.
                                     Defaults to the latest.

    Returns:     Hash: Text and author information.

    Example:
    # Get all latest case text
    >>> TestPlan.get_text(137)
    # Get all case text with version 4
    >>> TestPlan.get_text(137, 4)
    """
    tp = TestPlan.objects.get(plan_id = plan_id)
    test_plan_text = tp.get_text_with_version(plan_text_version = plan_text_version)
    if test_plan_text:
        return test_plan_text.serialize()
    else:
        return "No plan text with version '%s' found." % plan_text_version

def lookup_type_id_by_name(request, name):
    """DEPRECATED - CONSIDERED HARMFUL Use TestPlan.check_plan_type instead"""
    return check_plan_type(request = request, name = name)

def lookup_type_name_by_id(request, id):
    """DEPRECATED - CONSIDERED HARMFUL Use TestPlan.get_plan_type instead"""
    return get_plan_type(request = request, id = id)

@log_call
@user_passes_test(lambda u: u.has_perm('testplans.delete_testplantag'))
def remove_tag(request, plan_ids, tags):
    """
    Description: Remove a tag from a plan.

    Params:      $plan_ids - Integer/Array/String: An integer or alias representing the ID in the database,
                                                   an array of plan_ids, or a string of comma separated plan_ids.

                 $tag - String - A single tag to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove tag 'foo' from plan 1234
    >>> TestPlan.remove_tag(1234, 'foo')
    # Remove tag 'foo' and 'bar' from plan list [56789, 12345]
    >>> TestPlan.remove_tag([56789, 12345], ['foo', 'bar'])
    # Remove tag 'foo' and 'bar' from plan list '56789, 12345' with String
    >>> TestPlan.remove_tag('56789, 12345', 'foo, bar')
    """
    from tcms.apps.management.models import TestTag
    tps = TestPlan.objects.filter(
        plan_id__in = pre_process_ids(value = plan_ids)
    )
    tgs = TestTag.objects.filter(
        name__in = TestTag.string_to_list(tags)
    )

    for tp in tps:
        for tg in tgs:
            try:
                tp.remove_tag(tag = tg)
            except ObjectDoesNotExist:
                pass
            except:
                raise

    return

@log_call
@user_passes_test(lambda u: u.has_perm('testplans.add_testplantext'))
def store_text(request, plan_id, text, author = None):
    """
    Description: Update the document field of a plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database.
                 $text - String: Text for the document. Can contain HTML.
                 [$author] = Integer: (OPTIONAL) The numeric ID or the login of the author.
                      Defaults to logged in user.

    Returns:     Hash: The new text object hash.

    Example:
    >>> TestPlan.store_text(1234, 'Plan Text', 2207)
    """
    from django.contrib.auth.models import User

    tp = TestPlan.objects.get(plan_id = plan_id)

    if author:
        author = User.objects.get(id = author)
    else:
        author = request.user

    return tp.add_text(
        author = author,
        plan_text = text,
    ).serialize()

@log_call
@user_passes_test(lambda u: u.has_perm('testplans.change_testplan'))
def update(request, plan_ids, values):
    """
    Description: Updates the fields of the selected test plan.

    Params:      $plan_ids - Integer: A single TestPlan ID.

                 $values - Hash of keys matching TestPlan fields and the new values
                            to set each field to.
                 +-------------------------+----------------+
                 | Field                   | Type           |
                 +-------------------------+----------------+
                 | name                    | String         |
                 | type                    | Integer        |
                 | product                 | Integer        |
                 | default_product_version | Integer        |
                 | parent                  | Integer        |
                 | is_active               | Boolean        |
                 | env_group               | Integer        |
                 +-------------------------+----------------+

    Returns:     Hash: The updated test plan object.

    Example:
    # Update product to 61 for plan 207 and 208
    >>> TestCase.update([207, 208], {'product': 61})
    """
    from tcms.core import forms
    from tcms.apps.testplans.forms import XMLRPCEditPlanForm

    form = XMLRPCEditPlanForm(values)
    if values.get('default_product_version') and not values.get('product'):
        raise ValueError('Product value is required by default product version')

    if values.get('default_product_version') and values.get('product'):
        form.populate(product_id = values['product'])

    tps = TestPlan.objects.filter(pk__in = pre_process_ids(value = plan_ids))

    if form.is_valid():
        if form.cleaned_data['name']:
            tps.update(name = form.cleaned_data['name'])

        if form.cleaned_data['type']:
            tps.update(type = form.cleaned_data['type'])

        if form.cleaned_data['product']:
            tps.update(product = form.cleaned_data['product'])

        if form.cleaned_data['default_product_version']:
            tps.update(default_product_version = form.cleaned_data['default_product_version'])

        if form.cleaned_data['parent']:
            tps.update(parent = form.cleaned_data['parent'])

        if isinstance(form.cleaned_data['is_active'], int):
            tps.update(is_active = form.cleaned_data['is_active'])

        if form.cleaned_data['env_group']:
            for tp in tps:
                tp.clear_env_groups()
                tp.add_env_group(form.cleaned_data['env_group'])
    else:
        return forms.errors_to_list(form)

    query = {'pk__in': tps.values_list('pk', flat = True)}
    return TestPlan.to_xmlrpc(query)
