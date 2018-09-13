# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Compatibility wrappers for various library versions."""

from django.conf import settings


# NAME_FIELD
#
# The django-filter library renamed 'Filter.name' to 'Filter.field_name' in
# 1.1.
#
# DjangoFilterBackend

# The django-filter library changed the default strictness level in 2.0
#
# https://django-filter.readthedocs.io/en/master/guide/migration.html#migrating-to-2-0

if settings.ENABLE_REST_API:
    import django_filters  # noqa
    from django_filters import rest_framework  # noqa
    from rest_framework import exceptions  # noqa

    if django_filters.VERSION >= (1, 1):
        NAME_FIELD = 'field_name'
    else:
        NAME_FIELD = 'name'

    if django_filters.VERSION >= (2, 0):
        # TODO(stephenfin): Enable strict mode in API v2.0, possibly with a
        # bump in the minimum version of django-filter [1]
        #
        # [1] https://github.com/carltongibson/django-filter/pull/983
        class DjangoFilterBackend(rest_framework.DjangoFilterBackend):
            def filter_queryset(self, request, queryset, view):
                try:
                    return super().filter_queryset(request, queryset, view)
                except exceptions.ValidationError:
                    return queryset.none()
    else:
        DjangoFilterBackend = rest_framework.DjangoFilterBackend
