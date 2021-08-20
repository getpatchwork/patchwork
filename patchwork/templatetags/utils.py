# Patchwork - automated patch tracking system
# Copyright (C) 2021 Google LLC
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template

register = template.Library()


@register.filter
def verbose_name_plural(obj):
    return obj._meta.verbose_name_plural


@register.simple_tag
def is_editable(obj, user):
    return obj.is_editable(user)
