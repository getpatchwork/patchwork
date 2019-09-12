# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

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

    check_elements = []
    use_color = True
    for state in required[::-1]:
        if counts[state]:
            if use_color:
                use_color = False
                color = dict(Check.STATE_CHOICES).get(state)
            else:
                color = ''
            count = str(counts[state])
        else:
            color = ''
            count = '-'

        check_elements.append(
            '<span class="patchlistchecks {}">{}</span>'.format(
                color, count))

    check_elements.reverse()

    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join(titles),
        ''.join(check_elements)))


@register.filter(name='patch_commit_display')
def patch_commit_display(patch):
    commit = patch.commit_ref
    fmt = patch.project.commit_url_format

    if not fmt:
        return escape(commit)

    return mark_safe('<a href="%s">%s</a>' % (escape(fmt.format(commit)),
                                              escape(commit)))
