# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.utils.safestring import mark_safe

from patchwork.models import Check


register = template.Library()


@register.filter(name='series_tags')
def series_tags(series):
    counts = []
    titles = []

    for tag in [t for t in series.project.tags if t.show_column]:
        count = 0
        for patch in series.patches.with_tag_counts(series.project).all():
            count += getattr(patch, tag.attr_name)

        titles.append('%d %s' % (count, tag.name))
        if count == 0:
            counts.append('-')
        else:
            counts.append(str(count))

    return mark_safe(
        '<span title="%s">%s</span>' % (' / '.join(titles), ' '.join(counts))
    )


@register.filter(name='series_checks')
def series_checks(series):
    required = [Check.STATE_SUCCESS, Check.STATE_WARNING, Check.STATE_FAIL]
    titles = ['Success', 'Warning', 'Fail']
    counts = series.check_count

    check_elements = []
    for state in required[::-1]:
        if counts[state]:
            color = dict(Check.STATE_CHOICES).get(state)
            count = str(counts[state])
        else:
            color = ''
            count = '-'

        check_elements.append(
            f'<span class="patchlistchecks {color}">{count}</span>'
        )

    check_elements.reverse()

    return mark_safe(
        '<span title="%s">%s</span>'
        % (' / '.join(titles), ''.join(check_elements))
    )


@register.filter(name='series_interest')
def series_interest(series):
    reviews = series.interest_count
    review_title = (
        f'has {reviews} interested reviewers'
        if reviews > 0
        else 'no interested reviewers'
    )
    review_class = 'exists' if reviews > 0 else ''
    return mark_safe(
        '<span class="patchinterest %s" title="%s">%s</span>'
        % (review_class, review_title, reviews if reviews > 0 else '-')
    )
