"""
Development settings for patchwork project.

These are also used in unit tests.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

from __future__ import absolute_import

import django

from .base import *  # noqa

#
# Core settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#core-settings
#

# Security

SECRET_KEY = '00000000000000000000000000000000000000000000000000'

# Debugging

DEBUG = True

# Templates

if django.VERSION < (1, 8):
    # In Django 1.8+, this is only necessary if the value differs from
    # the value for 'DEBUG'
    TEMPLATE_DEBUG = True

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'PORT': '',
        'USER': os.getenv('PW_TEST_DB_USER', 'patchwork'),
        'PASSWORD': os.getenv('PW_TEST_DB_PASS', 'password'),
        'NAME': os.getenv('PW_TEST_DB_NAME', 'patchwork'),
    },
}

if os.getenv('PW_TEST_DB_TYPE', None) == 'postgres':
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

if django.VERSION >= (1, 7):
    DATABASES['default']['TEST'] = {
        'CHARSET': 'utf8',
    }
else:
    DATABASES['default']['TEST_CHARSET'] = 'utf8'

# Email

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#
# Third-party application settings
#

# django-debug-toolbar

if django.VERSION >= (1, 7):
    INSTALLED_APPS += [
        'debug_toolbar'
    ]

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # This should go first in the middleware classes
    MIDDLEWARE_CLASSES = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE_CLASSES

    INTERNAL_IPS = ['127.0.0.1', '::1']


#
# Patchwork settings
#

ENABLE_XMLRPC = True
