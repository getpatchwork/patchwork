"""
Development settings for patchwork project.

These are also used in unit tests.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

from __future__ import absolute_import

from .base import *  # noqa

#
# Core settings
# https://docs.djangoproject.com/en/1.11/ref/settings/#core-settings
#


ALLOWED_HOSTS = ['*']

SECRET_KEY = '00000000000000000000000000000000000000000000000000'  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.getenv('PW_TEST_DB_HOST', 'localhost'),
        'PORT': os.getenv('PW_TEST_DB_PORT', ''),
        'USER': os.getenv('PW_TEST_DB_USER', 'patchwork'),
        'PASSWORD': os.getenv('PW_TEST_DB_PASS', 'password'),
        'NAME': os.getenv('PW_TEST_DB_NAME', 'patchwork'),
        'TEST': {
            'CHARSET': 'utf8',
        },
    },
}

if os.getenv('PW_TEST_DB_TYPE', None) == 'postgres':
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
    DATABASES['default']['HOST'] = os.getenv('PW_TEST_DB_HOST', '')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#
# Auth settings
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth
#

# Use a faster, though less secure, password hasher for faster tests
# https://docs.djangoproject.com/es/1.11/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

#
# Third-party application settings
#

# django-debug-toolbar

INSTALLED_APPS += [
    'debug_toolbar'
]

DEBUG_TOOLBAR_PATCH_SETTINGS = False

# This should go first in the middleware classes
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

INTERNAL_IPS = [
    '127.0.0.1', '::1',
    '172.18.0.1'
]


#
# Patchwork settings
#

ENABLE_XMLRPC = True

ENABLE_REST_API = True
