# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


def _compile(value):
    regex, cls = value
    return re.compile(regex, re.M | re.I), cls


_patch_span_res = [_compile(x) for x in [
    (r'^(Index:?|diff|\-\-\-|\+\+\+|\*\*\*) .*$', 'p_header'),
    (r'^\+.*$', 'p_add'),
    (r'^-.*$', 'p_del'),
    (r'^!.*$', 'p_mod'),
]]

_patch_chunk_re = re.compile(
    r'^(@@ \-\d+(?:,\d+)? \+\d+(?:,\d+)? @@)(.*)$', re.M | re.I)

_comment_span_res = [_compile(x) for x in [
    (r'^\s*Signed-off-by: .*$', 'signed-off-by'),
    (r'^\s*Acked-by: .*$', 'acked-by'),
    (r'^\s*Nacked-by: .*$', 'nacked-by'),
    (r'^\s*Tested-by: .*$', 'tested-by'),
    (r'^\s*Reviewed-by: .*$', 'reviewed-by'),
    (r'^\s*From: .*$', 'from'),
    (r'^\s*&gt;.*$', 'quote'),
]]

_span = '<span class="%s">%s</span>'


@register.filter
def patchsyntax(patch):
    diff = escape(patch.diff).replace('\r\n', '\n')

    for (regex, cls) in _patch_span_res:
        diff = regex.sub(lambda x: _span % (cls, x.group(0)), diff)

    diff = _patch_chunk_re.sub(
        lambda x:
        _span % ('p_chunk', x.group(1)) + ' ' +
        _span % ('p_context', x.group(2)),
        diff)

    return mark_safe(diff)


@register.filter
def commentsyntax(submission):
    content = escape(submission.content)

    for (r, cls) in _comment_span_res:
        content = r.sub(lambda x: _span % (cls, x.group(0)), content)

    return mark_safe(content)
