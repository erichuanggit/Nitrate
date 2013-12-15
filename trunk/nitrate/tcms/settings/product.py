# Django settings for product env.

from common import *

# Debug settings
DEBUG = True
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

MEDIA_ROOT = '/usr/share/nitrate/media/'

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

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
EMAIL_HOST = 'smtp.corp.redhat.com'
EMAIL_FROM = 'noreply@redhat.com'

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

FOOTER_LINKS = (
 ('mailto:tcms-dev-list@redhat.com', 'Contact developers'),
 ('mailto:eng-ops@redhat.com', 'Request permissions'),
 ('https://bugzilla.redhat.com/enter_bug.cgi?product=TCMS&version=3.0', 'Report bug'),
 ('https://riddler.bne.redhat.com/TCMS-User_Guide/index.html', 'User guide'),
 ('http://survey.englab.nay.redhat.com/index.php?sid=14851&lang=en', 'Satisfaction Survey'),
 ('https://fedorahosted.org/nitrate/wiki', 'Release schedule'),
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

