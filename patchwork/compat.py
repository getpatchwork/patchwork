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
# https://django-filter.readthedocs.io/en/master/guide/migration.html#migrating-to-2-0

if settings.ENABLE_REST_API:
    import django_filters  # noqa

    if django_filters.VERSION >= (1, 1):
        NAME_FIELD = 'field_name'
    else:
        NAME_FIELD = 'name'
