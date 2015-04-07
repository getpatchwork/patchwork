# Django settings for patchwork project.

import os

import django

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

#
# Core settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#core-settings
#

# Models

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'patchwork',
)

# HTTP

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

if django.VERSION < (1, 7):
    MIDDLEWARE_CLASSES.append('django.middleware.doc.XViewMiddleware')
else:
    MIDDLEWARE_CLASSES.append(
        'django.contrib.admindocs.middleware.XViewMiddleware')
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Debugging

DEBUG = True

if django.VERSION >= (1, 7):
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Email

ADMINS = (
     ('Jeremy Kerr', 'jk@ozlabs.org'),
)

MANAGERS = ADMINS

# Databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'patchwork',
    },
}

# File Uploads

MEDIA_ROOT = os.path.join(
    ROOT_DIR, 'lib', 'python', 'django', 'contrib', 'admin', 'media')

# Globalization

TIME_ZONE = 'Australia/Canberra'

LANGUAGE_CODE = 'en-au'

USE_I18N = True

# URLs

ROOT_URLCONF = 'patchwork.urls'

# Security

# Make this unique, and don't share it with anybody.
SECRET_KEY = '00000000000000000000000000000000000000000000000000'

# Templates

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    os.path.join(ROOT_DIR, 'templates'),
)


#
# Auth settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#auth
#

LOGIN_URL = '/user/login/'
LOGIN_REDIRECT_URL = '/user/'


#
# Sites settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#sites
#

SITE_ID = 1


#
# Static files settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#static-files
#

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(ROOT_DIR, 'htdocs'),
]


#
# Patchwork settings
#

DEFAULT_PATCHES_PER_PAGE = 100
DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'

CONFIRMATION_VALIDITY_DAYS = 7

NOTIFICATION_DELAY_MINUTES = 10
NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

# Set to True to enable the Patchwork XML-RPC interface
ENABLE_XMLRPC = False

# set to True to enable redirections or URLs from previous versions
# of patchwork
COMPAT_REDIR = True

# Set to True to always generate https:// links instead of guessing
# the scheme based on current access. This is useful if SSL protocol
# is terminated upstream of the server (e.g. at the load balancer)
FORCE_HTTPS_LINKS = False

try:
    from local_settings import *
except ImportError, ex:
    import sys
    sys.stderr.write(\
            ("settings.py: error importing local settings file:\n" + \
            "\t%s\n" + \
            "Do you have a local_settings.py module?\n") % str(ex))
    raise
