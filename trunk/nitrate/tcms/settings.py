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

# Django default settings for tcms project.

import os.path

# Debug settings

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = False

# Administrators error report email settings

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Database settings

DATABASE_ENGINE = 'sqlite3'     # 'postgresql_psycopg2', 'postgresql',
                                # 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'dev.db'        # Or path to database file if using sqlite3.
DATABASE_USER = ''              # Not used with sqlite3.
DATABASE_PASSWORD = ''          # Not used with sqlite3.
DATABASE_HOST = ''              # Set to empty string for localhost.
                                # Not used with sqlite3.
DATABASE_PORT = ''              # Set to empty string for default.
                                # Not used with sqlite3.

DATABASE_OPTIONS = {}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'media').replace('\\','/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# URL prefix for admin absolute URL
ADMIN_PREFIX = '/admin'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 't&xaxmguqrfksbmrn3ltt8xcb61k71dzsr6a58k8-^$$!92k_x'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'tcms.core.lib.django-pagination.pagination.middleware.PaginationMiddleware',
)

ROOT_URLCONF = 'tcms.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), '..', 'templates/').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'kobo.django.xmlrpc',
    'tcms.profiles',
    'tcms.core',
    'tcms.core.contrib.auth',
    'tcms.core.contrib.comments',
    'tcms.core.contrib.logs',
    'tcms.management',
    'tcms.testcases',
    'tcms.testplans',
    'tcms.testruns',
    'tcms.testreviews',
    'tcms.core.lib.django-pagination.pagination'
)

# RequestContext settings

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.debug',
    'tcms.core.context_processors.admin_prefix_processor',
    'tcms.core.context_processors.admin_media_prefix_processor',
    'tcms.core.context_processors.auth_backend_processor',
    'tcms.core.context_processors.request_contents_processor',
    'tcms.core.context_processors.settings_processor',
)

# XML-RPC methods

XMLRPC_METHODS = {
    'TCMS_XML_RPC': (
        ('tcms.xmlrpc.auth', 'Auth'),
        ('tcms.xmlrpc.build', 'Build'),
        ('tcms.xmlrpc.env', 'Env'),
        ('tcms.xmlrpc.product', 'Product'),
        ('tcms.xmlrpc.testcase', 'TestCase'),
        ('tcms.xmlrpc.testcaserun', 'TestCaseRun'),
        ('tcms.xmlrpc.testopia', 'Testopia'),
        ('tcms.xmlrpc.testplan', 'TestPlan'),
        ('tcms.xmlrpc.testrun', 'TestRun'),
        ('tcms.xmlrpc.user', 'User'),
    ),
}

XMLRPC_TEMPLATE = 'xmlrpc.html'

# wadofstuff serializer settings
# http://code.google.com/p/wadofstuff/wiki/DjangoFullSerializers
SERIALIZATION_MODULES = {
    'json': 'tcms.core.lib.wadofstuff.django.serializers.json',
}

# Cache backend
CACHE_BACKEND = 'locmem://'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Authentication backends
# For the login/register/logout reaon, we only support the internal auth backends.
# Here we use TCMS Email Auth Backend by default
AUTHENTICATION_BACKENDS = (
    'tcms.core.contrib.auth.backends.DBModelBackend',
)

# Debug settings
# It can be show in console when DEBUG_PROPAGATE_EXCEPTIONS is True

# Debug log file, default is output to console
DEBUG_LOG_FILE = '/var/log/shipshape.log'
# Debug level is following:
# - 0 is None
# - 1 is Info
# - 5 is Error
DEBUG_LEVEL = 0

# Attachement file download path
# it could be spcified to a different out of MEDIA_URL
# FILE_UPLOAD_DIR = path.join(MEDIA_DIR, 'uploads').replace('\\','/'),
FILE_UPLOAD_DIR = '/var/tmp/uploads'

# Bugzilla author xmlrpc url
BUGZILLA3_RPC_SERVER = ''
BUGZILLA_URL = ''

# Needed by django.core.context_processors.debug:
# See http://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-debug

INTERNAL_IPS = ('127.0.0.1', )

# Defene the custom comment app
# http://docs.djangoproject.com/en/dev/ref/contrib/comments/custom/

COMMENTS_APP = 'tcms.core.contrib.comments'

# Mail settings

# Set the default send mail address
# See http://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_FROM = 'noreply@foo.com'
EMAIL_SUBJECT_PREFIX = '[TCMS] '

# Maximum upload file size, default set to 5MB.
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = 5242880

# Site-specific messages

# The site can supply optional "message of the day" style
# banners, similar to /etc/motd
# They are fragments of HTML.

# This one, if set, is shown on the front page.
# It is only shown to authenticated users
#MOTD_AUTH = """<p>This is a development instance of the TCMS</p>
# <p>(this is MOTD_AUTH)</p>"""

# This one, if set, is shown on the login screen.
# It is shown to unauthenticated users
#MOTD_LOGIN = """<p>This is a development instance of the TCMS</p> 
# <p>(this is MOTD_LOGIN)</p>"""


# Kerberos settings
KRB5_REALM = ''

# Testopia XML version
TESTOPIA_XML_VERSION = '1.1'

# First run - to detemine need port user or not.
FIRST_RUN = True

# Enable the administrator delete permission
# In another word it's set the admin to super user or not.
SET_ADMIN_AS_SUPERUSER = False

# The URLS will be list in footer
# Example:
#FOOTER_LINKS = (
#   ('mailto:nitrate-dev-list@example.com', 'Contact Us'),
#   ('mailto:nitrate-admin@example.com', 'Request Permission'),
#   ('http://foo.com', 'foo')
#)
FOOTER_LINKS = ()
