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

# Django settings for tcms project.

import django.conf.global_settings as DEFAULT_SETTINGS
import os.path


DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Administrators error report email settings
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# URL prefix for admin absolute URL
ADMIN_PREFIX = '/admin'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/usr/share/nitrate/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static').replace('\\','/')),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^8y!)$0t7yq2+65%&_#@i^_o)eb3^q--y_$e7a_=t$%$1i)zuv'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'tcms.core.middleware.CsrfDisableMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tcms.core.lib.django-pagination.pagination.middleware.PaginationMiddleware',
)

ROOT_URLCONF = 'tcms.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'tcms.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates/').replace('\\','/')),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'kobo.django.xmlrpc',
    'tcms.apps.profiles',
    'tcms.core',
    'tcms.core.contrib.auth',
    'tcms.core.contrib.comments',
    'tcms.core.logs',
    'tcms.apps.management',
    'tcms.apps.testcases',
    'tcms.apps.testplans',
    'tcms.apps.testruns',
    'tcms.apps.testreviews',
    'tcms.core.lib.django-pagination.pagination',

    'tcms.integration.djqpid',
    'tcms.integration.apps.errata',
    'tcms.core.contrib.linkreference',

    'tcms.integration.apps.bugzilla',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'tcms.core.context_processors.admin_prefix_processor',
    'tcms.core.context_processors.auth_backend_processor',
    'tcms.core.context_processors.request_contents_processor',
    'tcms.core.context_processors.settings_processor',
)

#
# Default apps settings
#

# Define the custom comment app
# http://docs.djangoproject.com/en/dev/ref/contrib/comments/custom/

COMMENTS_APP = 'tcms.core.contrib.comments'

# Define the custom profile models
AUTH_PROFILE_MODULE = 'profiles.UserProfile'

#
# XML-RPC interface settings
#
# XML-RPC methods
XMLRPC_METHODS = {
    'TCMS_XML_RPC': (
        ('tcms.xmlrpc.auth', 'Auth'),
        ('tcms.xmlrpc.build', 'Build'),
        ('tcms.xmlrpc.env', 'Env'),
        ('tcms.xmlrpc.product', 'Product'),
        ('tcms.xmlrpc.testcase', 'TestCase'),
        ('tcms.xmlrpc.testcaserun', 'TestCaseRun'),
        ('tcms.xmlrpc.testcaseplan', 'TestCasePlan'),
        ('tcms.xmlrpc.testopia', 'Testopia'),
        ('tcms.xmlrpc.testplan', 'TestPlan'),
        ('tcms.xmlrpc.testrun', 'TestRun'),
        ('tcms.xmlrpc.user', 'User'),
        ('tcms.xmlrpc.version', 'Version'),
        ('tcms.xmlrpc.tag', 'Tag'),
    ),
}

XMLRPC_TEMPLATE = 'xmlrpc.html'

# Cache backend
CACHE_BACKEND = 'locmem://'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# wadofstuff serializer settings
# http://code.google.com/p/wadofstuff/wiki/DjangoFullSerializers
SERIALIZATION_MODULES = {
    'json': 'wadofstuff.django.serializers.json',
}

# Needed by django.core.context_processors.debug:
# See http://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-debug
INTERNAL_IPS = ('127.0.0.1', )

# Authentication backends
# For the login/register/logout reaon, we only support the internal auth backends.
AUTHENTICATION_BACKENDS = (
    'tcms.core.contrib.auth.backends.DBModelBackend',
)

#
# Mail settings
#
# Set the default send mail address
# See http://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_FROM = 'noreply@foo.com'
EMAIL_SUBJECT_PREFIX = '[TCMS] '

EMAILS_FOR_DEBUG = []

# TCMS email behavior settings
PLAN_EMAIL_TEMPLATE = 'mail/change_plan.txt'
PLAN_DELELE_EMAIL_TEMPLATE = 'mail/delete_plan.txt'
CASE_EMAIL_TEMPLATE = 'mail/edit_case.txt'
CASE_DELETE_EMAIL_TEMPLATE = 'mail/delete_case.txt'

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

# Pagination
PLAN_RUNS_PAGE_SIZE = 20

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

# The URLS will be list in footer
# Example:
#FOOTER_LINKS = (
#   ('mailto:nitrate-dev-list@example.com', 'Contact Us'),
#   ('mailto:nitrate-admin@example.com', 'Request Permission'),
#   ('http://foo.com', 'foo')
#)
FOOTER_LINKS = ()

# Attachement file download path
# it could be spcified to a different out of MEDIA_URL
# FILE_UPLOAD_DIR = path.join(MEDIA_DIR, 'uploads').replace('\\','/'),
FILE_UPLOAD_DIR = '/var/nitrate/uploads'

#
# Installation settings
#
# First run - to detemine need port user or not.
FIRST_RUN = True

# Enable the administrator delete permission
# In another word it's set the admin to super user or not.
SET_ADMIN_AS_SUPERUSER = False

#
# Authentication backend settings
#
# Bugzilla author xmlrpc url
# Required by bugzilla authentication backend
BUGZILLA3_RPC_SERVER = ''
BUGZILLA_URL = ''

# Turn on/off listening signals sent by models.
LISTENING_MODEL_SIGNAL = True

# Kerberos settings
# Required by kerberos authentication backend
KRB5_REALM = ''

# Integration with Errata system, used to linkify the Errata ID
# A valid Errata URL:
# https://errata.devel.example.com/errata/stateview/{Errata ID}
ERRATA_URL_PREFIX = ''

# user guide url:
USER_GUIDE_URL = ''

# Default page size for showing each possible query result. This provides a
# consistent user experiece to users.
DEFAULT_PAGE_SIZE = 20

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
