"""
Development settings for patchwork project.

These are also used in unit tests.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

import django

from base import *

#
# Core settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#core-settings
#

# Security

SECRET_KEY = '00000000000000000000000000000000000000000000000000'

# Debugging

DEBUG = True

# Templates

TEMPLATE_DEBUG = True

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'PORT': '',
        'USER': os.environ['PW_TEST_DB_USER'],
        'PASSWORD': os.environ['PW_TEST_DB_PASS'],
        'NAME': 'patchwork',
        'TEST_CHARSET': 'utf8',
    },
}

#
# Patchwork settings
#

ENABLE_XMLRPC = True
