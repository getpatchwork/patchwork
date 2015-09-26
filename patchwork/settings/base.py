"""
Base settings for patchwork project.
"""

import os

import django

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir)

#
# Core settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#core-settings
#

# Models

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'patchwork',
]

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

# Globalization

TIME_ZONE = 'Australia/Canberra'

LANGUAGE_CODE = 'en-au'

USE_I18N = True

# Testing

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# URLs

ROOT_URLCONF = 'patchwork.urls'

# Templates

TEMPLATE_DIRS = (
    os.path.join(ROOT_DIR, 'templates'),
)

# Email

DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'

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

CONFIRMATION_VALIDITY_DAYS = 7

NOTIFICATION_DELAY_MINUTES = 10
NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

# Set to True to enable the Patchwork XML-RPC interface
ENABLE_XMLRPC = False

# Set to True to enable redirections or URLs from previous versions
# of patchwork
COMPAT_REDIR = True

# Set to True to always generate https:// links instead of guessing
# the scheme based on current access. This is useful if SSL protocol
# is terminated upstream of the server (e.g. at the load balancer)
FORCE_HTTPS_LINKS = False
