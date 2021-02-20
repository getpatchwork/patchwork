"""
Sample production-ready settings for patchwork project.

Most of these are commented out as they will be installation dependent.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

import os

from .base import *  # noqa

#
# Core settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#core-settings
#

# Security
#
# You'll need to replace this to a random string. The following python code can
# be used to generate a secret key:
#
#      import string
#      import secrets
#
#      chars = string.ascii_letters + string.digits + string.punctuation
#      print("".join([secrets.choice(chars) for i in range(50)]))

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Email
#
# Replace this with your own details

EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = os.getenv('EMAIL_PORT', 25)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

ADMINS = (
    # Add administrator contact details in the form:
    # ('Jeremy Kerr', 'jk@ozlabs.org'),
)

# Database
#
# If you're using a postgres database, connecting over a local unix-domain
# socket, then the following setting should work for you. Otherwise,
# see https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATABASE_NAME', ''),
        'USER': os.environ.get('DATABASE_USER', ''),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', ''),
        'PORT': os.environ.get('DATABASE_PORT', ''),
    },
}

#
# Static files settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#static-files
# https://docs.djangoproject.com/en/2.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
#

STATIC_ROOT = os.environ.get('STATIC_ROOT', '/srv/patchwork/htdocs/static')

STATICFILES_STORAGE = (
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage')
