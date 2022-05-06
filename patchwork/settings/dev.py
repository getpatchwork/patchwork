"""
Development settings for patchwork project.

These are also used in unit tests.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

from .base import *  # noqa

try:
    import dbbackup
except ImportError:
    dbbackup = None

try:
    import debug_toolbar
except ImportError:
    debug_toolbar = None

#
# Core settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#core-settings
#

ADMINS = (('Joe Bloggs', 'jbloggs@example.com'),)

ALLOWED_HOSTS = ['*']

SECRET_KEY = '00000000000000000000000000000000000000000000000000'  # noqa

DEBUG = True

if DATABASES['default']['ENGINE'] == 'mysql':  # noqa: F405
    DATABASES['default']['TEST'] = {'CHARSET': 'utf8'}  # noqa: F405

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#
# Auth settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth
#

# Use a faster, though less secure, password hasher for faster tests
# https://docs.djangoproject.com/en/2.2/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

#
# Third-party application settings
#

# django-debug-toolbar

if debug_toolbar:
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # This should go first in the middleware classes
    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE  # noqa: F405

    INTERNAL_IPS = ['127.0.0.1', '::1', '172.18.0.1']

# django-dbbackup

if dbbackup:
    INSTALLED_APPS += [
        'dbbackup',
    ]

    DBBACKUP_STORAGE_OPTIONS = {'location': '.backups'}

#
# Patchwork settings
#

ENABLE_XMLRPC = True

ENABLE_REST_API = True
