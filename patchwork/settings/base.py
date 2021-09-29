"""
Base settings for patchwork project.
"""

import os

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir)

#
# Core settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#core-settings
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

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TIME_ZONE = 'Australia/Canberra'

USE_I18N = False

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ROOT_URLCONF = 'patchwork.urls'

_TEMPLATE_DIRS = [
    os.path.join(ROOT_DIR, 'templates'),
]

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
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'patchwork.context_processors.site',
                'patchwork.context_processors.version',
            ],
        },
    },
]

# TODO(stephenfin): Consider changing to BigAutoField when we drop support for
# Django < 3.2
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DEFAULT_FROM_EMAIL = 'Patchwork <patchwork@patchwork.example.com>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL

#
# Auth settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth
#

LOGIN_URL = 'auth_login'

LOGIN_REDIRECT_URL = 'user-profile'


#
# Sites settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#sites
#

SITE_ID = 1


#
# Static files settings
# https://docs.djangoproject.com/en/2.2/ref/settings/#static-files
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
        'patchwork.api.filters.DjangoFilterBackend',
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
    'NON_FIELD_ERRORS_KEY': 'detail',
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
            'level': 'WARNING',
            'propagate': True,
        },
        'patchwork.parser': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'patchwork.management.commands.parsearchive': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'patchwork.management.commands.parsemail': {
            'handlers': ['console', 'mail_admins'],
            'level': 'WARNING',
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
MAX_REST_RESULTS_PER_PAGE = 250

# Set to True to enable redirections or URLs from previous versions
# of patchwork
COMPAT_REDIR = True

# Set to True to always generate https:// links instead of guessing
# the scheme based on current access. This is useful if SSL protocol
# is terminated upstream of the server (e.g. at the load balancer)
FORCE_HTTPS_LINKS = False

# Set to True to hide admin details from the about page (/about)
ADMINS_HIDE = False
