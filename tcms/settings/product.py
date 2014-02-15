# Django settings for product env.

from common import *

# Debug settings
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'nitrate',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'nitrate',
        'PASSWORD': 'nitrate',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# add RemoteUserMiddleWare if kerberos authentication is enabled
MIDDLEWARE_CLASSES += (
#    'django.contrib.auth.middleware.RemoteUserMiddleware',
)

# Remote kerberos authentication backends
#AUTHENTICATION_BACKENDS = (
#    'tcms.core.contrib.auth.backends.ModAuthKerbBackend',
#)

# Kerberos realm
#KRB5_REALM = 'EXAMPLE.COM'

# Bugzilla integration setttings
# Config following settings if your want to integrate with bugzilla
BUGZILLA3_RPC_SERVER = ''
BUGZILLA_URL = ''
BUGZILLA_USER = ''
BUGZILLA_PASSWORD = ''

# Set the default send mail address
EMAIL_HOST = 'smtp.example.com'
EMAIL_FROM = 'noreply@example.com'

# Site-specific messages

# This one, if set, is shown on the front page.
# It is only shown to authenticated users
MOTD_AUTH = """
<p>This is the development server for the production instance of the TCMS, 
connected to a copy of the testopia database.</p>
"""

# First run - to detemine need port user or not.
FIRST_RUN = False

MOTD_LOGIN = """<p>This is the development server of the TCMS (for testing).</p>
<p>Please use your kerberos user name and password.</p>
"""
# You can add a help link on the footer of home page as following format:
# ('http://foo.com', 'foo')
FOOTER_LINKS = (
 ('/xmlrpc/', 'XML-RPC service'),
)

# added for nitrate3.4 compatibility
DEFAULT_GROUPS = ['default']
TESTOPIA_XML_VERSION = '1.0'

# admin settings
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# user guide URL
USER_GUIDE_URL = ""

DEFAULT_PAGE_SIZE = 100

