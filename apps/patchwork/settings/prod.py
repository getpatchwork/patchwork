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

# SECRET_KEY = '00000000000000000000000000000000000000000000000000'

# Email

# ADMINS = (
#      ('Jeremy Kerr', 'jk@ozlabs.org'),
# )

# Database

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'patchwork',
#     },
# }

# File Uploads

# MEDIA_ROOT = os.path.join(
#     ROOT_DIR, 'lib', 'python', 'django', 'contrib', 'admin', 'media')


#
# Static files settings
# https://docs.djangoproject.com/en/1.6/ref/settings/#static-files
#

# STATIC_ROOT = '/srv/patchwork/htdocs'


#
# Custom user overrides (for legacy)
#

try:
    from local_settings import *
except ImportError, ex:
    import sys
    sys.stderr.write(\
            ("settings.py: error importing local settings file:\n" + \
            "\t%s\n" + \
            "Do you have a local_settings.py module?\n") % str(ex))
    raise
