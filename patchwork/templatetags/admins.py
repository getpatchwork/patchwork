# Patchwork - automated patch tracking system
# Copyright (C) 2020 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag()
def site_admins():
    admins = [
        f'{admin[0]} &lt;<a href="mailto:{admin[1]}">{admin[1]}</a>&gt;'
        for admin in settings.ADMINS
    ]

    if not admins:
        return ''

    if len(admins) == 1:
        return mark_safe(admins[0])

    return mark_safe(', '.join(admins[:-2]) + admins[-2] + ' or ' + admins[-1])
