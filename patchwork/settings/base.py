"""
Base settings for patchwork project.
"""

import os

import django

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir)

#
# Core settings
# https://docs.djangoproject.com/en/1.8/ref/settings/#core-settings
#

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'patchwork',
]

_MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if django.VERSION >= (1, 7):
    _MIDDLEWARE_CLASSES += [
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    ]


if django.VERSION >= (1, 10):
    MIDDLEWARE = _MIDDLEWARE_CLASSES
else:
    MIDDLEWARE_CLASSES = _MIDDLEWARE_CLASSES

TIME_ZONE = 'Australia/Canberra'

LANGUAGE_CODE = 'en-au'

USE_I18N = True

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ROOT_URLCONF = 'patchwork.urls'

_TEMPLATE_DIRS = [
    os.path.join(ROOT_DIR, 'templates'),
]

if django.VERSION >= (1, 8):
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': _TEMPLATE_DIRS,
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                    'patchwork.context_processors.site',
                    'patchwork.context_processors.version',
                ],
            },
        },
    ]
else:
    TEMPLATE_DIRS = _TEMPLATE_DIRS
    TEMPLATE_CONTEXT_PROCESSORS = [
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.static',
        'django.core.context_processors.tz',
        'django.contrib.messages.context_processors.messages',
        'patchwork.context_processors.site',
        'patchwork.context_processors.version',
    ]


DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL

#
# Auth settings
# https://docs.djangoproject.com/en/1.8/ref/settings/#auth
#

LOGIN_URL = 'auth_login'

LOGIN_REDIRECT_URL = 'user-profile'


#
# Sites settings
# https://docs.djangoproject.com/en/1.8/ref/settings/#sites
#

SITE_ID = 1


#
# Static files settings
# https://docs.djangoproject.com/en/1.8/ref/settings/#static-files
#

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(ROOT_DIR, 'htdocs'),
]

#
# Third-party application settings
#

# rest_framework

try:
    # django rest framework isn't a standard package in most distros, so
    # don't make it compulsory
    import rest_framework  # NOQA

    INSTALLED_APPS += [
        'rest_framework',
        'rest_framework.authtoken',
        'django_filters',
    ]
except ImportError:
    pass


REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS':
        'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_PAGINATION_CLASS': 'patchwork.api.base.LinkHeaderPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'patchwork.compat.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'SEARCH_PARAM': 'q',
    'ORDERING_PARAM': 'order',
}

#
# Logging settings
#

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'email': {
            'format': '== Mail\n\n%(mail)s\n\n== Traceback\n',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'email',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'patchwork.parser': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'patchwork.management.commands': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

#
# Patchwork settings
#

DEFAULT_ITEMS_PER_PAGE = 100

CONFIRMATION_VALIDITY_DAYS = 7

NOTIFICATION_DELAY_MINUTES = 10

NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

# Set to True to enable the Patchwork XML-RPC interface
ENABLE_XMLRPC = False

# Set to True to enable the Patchwork REST API
ENABLE_REST_API = True

REST_RESULTS_PER_PAGE = 30

# Set to True to enable redirections or URLs from previous versions
# of patchwork
COMPAT_REDIR = True

# Set to True to always generate https:// links instead of guessing
# the scheme based on current access. This is useful if SSL protocol
# is terminated upstream of the server (e.g. at the load balancer)
FORCE_HTTPS_LINKS = False
