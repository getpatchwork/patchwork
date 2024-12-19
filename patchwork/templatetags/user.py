# Patchwork - automated patch tracking system
# Copyright (C) 2024 Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def userfy(user):
    if user.first_name and user.last_name:
        linktext = escape(f'{user.first_name} {user.last_name}')
    elif user.email:
        linktext = escape(user.email)
    else:
        linktext = escape(user.username)

    return mark_safe(linktext)
