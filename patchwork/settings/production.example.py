"""
Sample production-ready settings for patchwork project.

Most of these are commented out as they will be installation dependent.

Design based on:
    http://www.revsys.com/blog/2014/nov/21/recommended-django-project-layout/
"""

from base import *

#
# Core settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#core-settings
#

# Security
#
# You'll need to replace this to a random string. The following python code can
# be used to generate a secret key:
#
#      import string, random
#      chars = string.letters + string.digits + string.punctuation
#      print repr("".join([random.choice(chars) for i in range(0,50)]))

# SECRET_KEY = '00000000000000000000000000000000000000000000000000'

# Email
#
# Replace this with your own details

ADMINS = (
#    ('Jeremy Kerr', 'jk@ozlabs.org'),
)

DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

# Database
#
# If you're using a postgres database, connecting over a local unix-domain
# socket, then the following setting should work for you. Otherwise,
# see https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'patchwork',
    },
}

#
# Static files settings
# https://docs.djangoproject.com/en/1.7/ref/settings/#static-files
#

STATIC_ROOT = '/srv/patchwork/htdocs/static'

