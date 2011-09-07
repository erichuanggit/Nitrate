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

from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# XML RPC handler
from kobo.django.xmlrpc.views import XMLRPCHandlerFactory
xmlrpc_handler = XMLRPCHandlerFactory('TCMS_XML_RPC')

urlpatterns = patterns('',
    # Example:
    # (r'^tcms/', include('tcms.foo.urls')),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    # Index and static zone
    (r'^$', 'tcms.core.views.index'),
    (r'^search/$', 'tcms.core.views.search'),
    (r'^xmlrpc/$', xmlrpc_handler),
    
    # Ajax call responder
    (r'^ajax/update/$', 'tcms.core.ajax.update'),
    (r'^ajax/form/$', 'tcms.core.ajax.form'),
    (r'^ajax/get-prod-relate-obj/$', 'tcms.core.ajax.get_prod_related_obj_json'),
    (r'^management/getinfo/$', 'tcms.core.ajax.info'),
    (r'^management/tags/$', 'tcms.core.ajax.tag'), 
    
    # Attached file zone
    (r'^management/uploadfile/$', 'tcms.core.files.upload_file'),
    (r'^management/checkfile/(?P<file_id>\d+)/$', 'tcms.core.files.check_file'),
    (r'^management/deletefile/(?P<file_id>\d+)/$', 'tcms.core.files.delete_file'),
    
    (r'^comments/post/', 'tcms.core.contrib.comments.views.post'),
    (r'^comments/list/', 'tcms.core.contrib.comments.views.all'),
    (r'^comments/delete/', 'tcms.core.contrib.comments.views.delete'),
    
    # Account information zone, such as login method
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'tcms.core.contrib.auth.views.logout'),
    (r'^accounts/register/$', 'tcms.core.contrib.auth.views.register'),
    (r'^accounts/confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', 'tcms.core.contrib.auth.views.confirm'),
    (r'^accounts/changepassword/$', 'django.contrib.auth.views.password_change'),
    (r'^accounts/changepassword/done/$', 'django.contrib.auth.views.password_change_done'),
    (r'^accounts/passwordreset/$', 'django.contrib.auth.views.password_reset'),
    (r'^accounts/passwordreset/done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^accounts/passwordreset/confirm//(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^accounts/profile/$', 'tcms.profiles.views.redirect_to_profile'), # Hacking for default url after login
    (r'^accounts/(?P<username>[\w.@+-]+)/profile/$', 'tcms.profiles.views.profile'),
    (r'^accounts/(?P<username>[\w.@+-]+)/bookmarks/$', 'tcms.profiles.views.bookmark'),
    (r'^accounts/(?P<username>[\w.@+-]+)/recent/$', 'tcms.profiles.views.recent'),
    
    # Testplans zone
    (r'^plan/new/$', 'tcms.testplans.views.new'),
    (r'^plans/$', 'tcms.testplans.views.all'),
    (r'^plans/treeview/$', 'tcms.testplans.views.tree_view'),
    (r'^plans/clone/$', 'tcms.testplans.views.clone'),
    (r'^plans/component/$', 'tcms.testplans.views.component'),
    (r'^plan/(?P<plan_id>\d+)/$', 'tcms.testplans.views.get'),
    (r'^plan/(?P<plan_id>\d+)/delete/$', 'tcms.testplans.views.delete'),
    (r'^plan/(?P<plan_id>\d+)/chooseruns/$', 'tcms.testplans.views.choose_run'),
    (r'^plan/(?P<plan_id>\d+)/edit/$', 'tcms.testplans.views.edit'),
    (r'^plan/(?P<plan_id>\d+)/attachment/$', 'tcms.testplans.views.attachment'),
    (r'^plan/(?P<plan_id>\d+)/history/$', 'tcms.testplans.views.text_history'),
    (r'^plan/(?P<plan_id>\d+)/cases/$', 'tcms.testplans.views.cases'),
    
    # Testcases zone
    (r'^case/new/$', 'tcms.testcases.views.new'),
    (r'^cases/$', 'tcms.testcases.views.all'),
    (r'^cases/automated/$', 'tcms.testcases.views.automated'),
    (r'^cases/component/$', 'tcms.testcases.views.component'),
    (r'^cases/clone/$', 'tcms.testcases.views.clone'),
    (r'^cases/printable/$', 'tcms.testcases.views.printable'),
    (r'^cases/export/$', 'tcms.testcases.views.export'),
    (r'^case/(?P<case_id>\d+)/$', 'tcms.testcases.views.get'),
    (r'^case/(?P<case_id>\d+)/edit/$', 'tcms.testcases.views.edit'),
    (r'^case/(?P<case_id>\d+)/history/$', 'tcms.testcases.views.text_history'),
    (r'^case/(?P<case_id>\d+)/attachment/$', 'tcms.testcases.views.attachment'),
    (r'^case/(?P<case_id>\d+)/log/$', 'tcms.testcases.views.get_log'),
    (r'^case/(?P<case_id>\d+)/bug/$', 'tcms.testcases.views.bug'),
    (r'^case/(?P<case_id>\d+)/plan/$', 'tcms.testcases.views.plan'),
    
    # Testruns zone
    (r'^run/new/$', 'tcms.testruns.views.new'),
    (r'^runs/$', 'tcms.testruns.views.all'),
    (r'^runs/env_value/$', 'tcms.testruns.views.env_value'),
    (r'^runs/clone/$', 'tcms.testruns.views.clone'),
    (r'^run/(?P<run_id>\d+)/$', 'tcms.testruns.views.get'),
    (r'^run/(?P<run_id>\d+)/clone/$','tcms.testruns.views.clone_with_filteredCaseRun'),
    (r'^run/(?P<run_id>\d+)/delete/$', 'tcms.testruns.views.delete'),
    (r'^run/(?P<run_id>\d+)/execute/$', 'tcms.testruns.views.execute'),
    (r'^run/(?P<run_id>\d+)/edit/$', 'tcms.testruns.views.edit'),
    (r'^run/(?P<run_id>\d+)/report/$', 'tcms.testruns.views.report'),
    (r'^run/(?P<run_id>\d+)/ordercase/$', 'tcms.testruns.views.order_case'),
    (r'^run/(?P<run_id>\d+)/changestatus/$', 'tcms.testruns.views.change_status'),
    (r'^run/(?P<run_id>\d+)/ordercaserun/$', 'tcms.testruns.views.order_case'),
    (r'^run/(?P<run_id>\d+)/removecaserun/$', 'tcms.testruns.views.remove_case_run'),
    (r'^run/(?P<run_id>\d+)/assigncase/$', 'tcms.testruns.views.assign_case'),
    (r'^run/(?P<run_id>\d+)/cc/$', 'tcms.testruns.views.cc'),
    (r'^run/(?P<run_id>\d+)/update/$', 'tcms.testruns.views.update_case_run_text'),
    (r'^run/(?P<run_id>\d+)/export/$', 'tcms.testruns.views.export'),
    
    (r'^caserun/(?P<case_run_id>\d+)/current/$', 'tcms.testruns.views.set_current'),
    (r'^caserun/(?P<case_run_id>\d+)/bug/$', 'tcms.testruns.views.bug'),
    (r'^caserun/comment-many/', 'tcms.core.ajax.comment_case_runs'),
    (r'^caserun/update-bugs-for-many/', 'tcms.core.ajax.update_bugs_to_caseruns'),
    
    # Review zone
    #(r'^plan/(?P<plan_id>\d+)/newreview/$', 'tcms.testreviews.views.new'),
    #(r'^review/(?P<review_id>\d+)/$', 'tcms.testreviews.views.get'),
    #(r'^review/(?P<review_id>\d+)/changestatus/$', 'tcms.testreviews.views.change_case_status'),
    
    # Management zone
    #(r'^management/$', 'tcms.management.views.index'),
    (r'^environment/groups/$', 'tcms.management.views.environment_groups'), 
    (r'^environment/group/edit/$', 'tcms.management.views.environment_group_edit'), 
    (r'^environment/properties/$', 'tcms.management.views.environment_properties'), 
    (r'^environment/properties/values/$', 'tcms.management.views.environment_property_values'), 
    
    # Management ajax zone
    
    # Report zone
    (r'^report/$', 'django.views.generic.simple.redirect_to', {'url': 'overall/'}),
    (r'^report/overall/$', 'tcms.report.views.overall'),
    (r'^report/product/(?P<product_id>\d+)/overview/$', 'tcms.report.views.overview'),
    (r'^report/product/(?P<product_id>\d+)/version/$', 'tcms.report.views.version'),
    (r'^report/product/(?P<product_id>\d+)/build/$', 'tcms.report.views.build'),
    (r'^report/product/(?P<product_id>\d+)/component/$', 'tcms.report.views.component'),
    
    (r'^report/custom/$', 'tcms.report.views.custom_search'),
    (r'^report/custom/details/$', 'tcms.report.views.custom_details'),
    url(r'^report/testing/$', 'tcms.report.views.view_test_run_report', name='testrun_report'),

    url(r'^advance-search/$', 'tcms.search.advance_search', name='advance_search'),
)

# Debug zone

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'(^|/)media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
    
    urlpatterns += patterns('tcms.core.utils.test_template',
        (r'^tt/(?P<template_name>.*)', 'test_template'),
    )

# Installation zone

if settings.FIRST_RUN:
    urlpatterns += patterns('tcms.install',
        (r'^install/$', 'install'),
        (r'^upgrade/$', 'upgrade'),
        (r'^create_groups/$', 'create_groups'),
        (r'^port_users/$', 'port_users'),
    )
