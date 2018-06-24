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
