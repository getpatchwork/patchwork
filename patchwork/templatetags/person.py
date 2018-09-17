# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from patchwork.filters import SubmitterFilter


register = template.Library()


@register.filter
def personify(person, project):

    if person.name:
        linktext = escape(person.name)
    else:
        linktext = escape(person.email)

    url = reverse('patch-list',
                  kwargs={'project_id': project.linkname})
    out = '<a href="%s?%s=%s">%s</a>' % (
        url, SubmitterFilter.param, escape(person.id), linktext)

    return mark_safe(out)
