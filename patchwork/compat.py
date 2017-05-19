# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# This file is part of the Patchwork package.
#
# Patchwork is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Patchwork is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Compatibility wrappers for various Django versions."""

import django
from django.conf import settings


# render_to_string
#
# The render_to_string function no longer accepts the dictionary and
# context_instance parameters in Django 1.10.
#
# https://docs.djangoproject.com/en/dev/releases/1.8/

if django.VERSION >= (1, 8):
    from django.template.loader import render_to_string  # noqa
else:
    from django.template import loader  # noqa
    from django.template import RequestContext  # noqa

    def render_to_string(template_name, context=None, request=None):
        context_instance = RequestContext(request) if request else None
        return loader.render_to_string(template_name, context,
                                       context_instance)


# DjangoFilterBackend
#
# The DjangoFilterBackend was provided in Django REST Framework from 3.0 to
# 3.4, was marked as pending deprecation in 3.5, was deprecated in 3.6 and will
# be removed in 3.7. However, the equivalent DjangoFilterBackend found in
# django-filter is only available since 1.0 of that package.
#
# http://www.django-rest-framework.org/topics/3.6-announcement/

if settings.ENABLE_REST_API:
    import rest_framework  # noqa

    if rest_framework.VERSION >= '3.5':
        from django_filters.rest_framework import DjangoFilterBackend  # noqa
    else:
        from rest_framework.filters import DjangoFilterBackend  # noqa


# LOOKUP_FIELD
#
# The django-filter library uses the 'lookup_expr' attribute to determine which
# lookup type to use, e.g. exact, gt, lt etc. However, until 0.13 this was
# called 'lookup_type', and 0.13 supported both but gave a deprecation warning.
# We need to support these versions for use with older versions of DRF.
#
# https://github.com/carltongibson/django-filter/blob/v0.13/django_filters\
#   /filters.py#L35-L36
if settings.ENABLE_REST_API:
    import django_filters  # noqa

    if django_filters.VERSION >= (1, 0):
        LOOKUP_FIELD = 'lookup_expr'
    else:
        LOOKUP_FIELD = 'lookup_type'


# reverse, reverse_lazy
#
# The reverse and reverse_lazy functions have been moved to django.urls in
# Django 1.10 and backwards compatible imports will be removed in Django 2.0

if django.VERSION >= (1, 10):
    from django.urls import NoReverseMatch  # noqa
    from django.urls import reverse  # noqa
    from django.urls import reverse_lazy  # noqa
else:
    from django.core.urlresolvers import NoReverseMatch  # noqa
    from django.core.urlresolvers import reverse  # noqa
    from django.core.urlresolvers import reverse_lazy  # noqa


# is_authenticated
#
# models.User.is_authenticated is now an attribute in Django 1.10 instead of a
# function
#
# https://docs.djangoproject.com/en/dev/releases/1.10/

def is_authenticated(user):
    if django.VERSION >= (1, 10):
        return user.is_authenticated
    else:
        return user.is_authenticated()
