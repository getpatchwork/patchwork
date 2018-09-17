# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def project_tags(context):
    tags = [t for t in context['project'].tags if t.show_column]
    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join([tag.name for tag in tags]),
        '/'.join([tag.abbrev for tag in tags])))
