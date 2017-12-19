# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
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

from __future__ import absolute_import

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

from patchwork.models import Check


register = template.Library()


@register.filter(name='patch_tags')
def patch_tags(patch):
    counts = []
    titles = []
    for tag in [t for t in patch.project.tags if t.show_column]:
        count = getattr(patch, tag.attr_name)
        titles.append('%d %s' % (count, tag.name))
        if count == 0:
            counts.append("-")
        else:
            counts.append(str(count))
    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join(titles),
        ' '.join(counts)))


@register.filter(name='patch_checks')
def patch_checks(patch):
    required = [Check.STATE_SUCCESS, Check.STATE_WARNING, Check.STATE_FAIL]
    titles = ['Success', 'Warning', 'Fail']
    counts = patch.check_count

    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join(titles),
        ' '.join([str(counts[state]) for state in required])))


@register.filter(name='state_class')
def state_class(state):
    return '-'.join(state.split())


@register.filter
@stringfilter
def msgid(value):
    return mark_safe(value.strip('<>'))
