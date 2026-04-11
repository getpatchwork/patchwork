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
            counts.append('-')
        else:
            counts.append(str(count))

    # counts are integers; titles contain tag names set by project maintainers
    return mark_safe(  # noqa: S308
        '<span title="%s">%s</span>' % (' / '.join(titles), ' '.join(counts))
    )


@register.filter(name='patch_checks')
def patch_checks(patch):
    required = [Check.STATE_SUCCESS, Check.STATE_WARNING, Check.STATE_FAIL]
    titles = ['Success', 'Warning', 'Fail']
    counts = patch.check_count

    check_elements = []
    all_empty = True
    for state in required:
        if counts[state]:
            all_empty = False
            break

    for state in required[::-1]:
        if counts[state]:
            color = dict(Check.STATE_CHOICES).get(state)
            count = str(counts[state])
        else:
            if all_empty:
                color = 'nochecks'
            else:
                color = ''
            count = '-'

        check_elements.append(
            f'<span class="patchlistchecks {color}">{count}</span>'
        )

    check_elements.reverse()

    # titles are hardcoded strings; check_elements contain hardcoded CSS class
    # names and integer counts
    return mark_safe(  # noqa: S308
        '<span title="%s">%s</span>'
        % (' / '.join(titles), ''.join(check_elements))
    )


@register.filter(name='patch_commit_display')
def patch_commit_display(patch):
    commit = patch.commit_ref
    fmt = patch.project.commit_url_format

    if not fmt:
        return escape(commit)

    # both the URL and display text are run through escape() above
    return mark_safe(  # noqa: S308
        '<a href="%s">%s</a>' % (escape(fmt.format(commit)), escape(commit))
    )


@register.filter(name='patch_labels')
def patch_labels(patch):

    def text_color(hex_color):
        """Generate the ideal text color given a background color.

        From https://www.w3.org/TR/AERT/#color-contrast
        """
        red, green, blue = [
            int(hex_color.lstrip('#')[i : i + 2], 16) for i in (0, 2, 4)
        ]
        brightness = (red * 299 + green * 587 + blue * 114) / 1000

        return '#000' if brightness >= 123 else '#fff'

    output = []
    for label in patch.labels.all():
        style = 'background-color: %s; color: %s' % (
            label.color,
            text_color(label.color),
        )
        output.append(
            '<span class="label" style="%s">%s</span>'
            % (style, escape(label.name))
        )

    # Label name is escaped above. Color is formatted in a way that
    # does not permit XSS
    return mark_safe(''.join(output))  # noqa: S308
