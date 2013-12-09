# Django settings for devel env.

from common import *

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = False

# Database settings
DATABASE_ENGINE = 'mysql'          # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'nitrate'          # Or path to database file if using sqlite3.
DATABASE_USER = 'nitrate'          # Not used with sqlite3.
DATABASE_PASSWORD = 'nitrate'      # Not used with sqlite3.
DATABASE_HOST = ''                 # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                 # Set to empty string for default. Not used with sqlite3.

# django-debug-toolbar settings
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INSTALLED_APPS += (
    'debug_toolbar',
)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}
