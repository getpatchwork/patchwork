# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
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

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.six.moves import map


register = template.Library()


def _compile(t):
    (r, str) = t
    return (re.compile(r, re.M | re.I), str)

_patch_span_res = list(map(_compile, [
    ('^(Index:?|diff|\-\-\-|\+\+\+|\*\*\*) .*$', 'p_header'),
    ('^\+.*$', 'p_add'),
    ('^-.*$', 'p_del'),
    ('^!.*$', 'p_mod'),
]))

_patch_chunk_re = \
    re.compile('^(@@ \-\d+(?:,\d+)? \+\d+(?:,\d+)? @@)(.*)$', re.M | re.I)

_comment_span_res = list(map(_compile, [
    ('^\s*Signed-off-by: .*$', 'signed-off-by'),
    ('^\s*Acked-by: .*$', 'acked-by'),
    ('^\s*Nacked-by: .*$', 'nacked-by'),
    ('^\s*Tested-by: .*$', 'tested-by'),
    ('^\s*Reviewed-by: .*$', 'reviewed-by'),
    ('^\s*From: .*$', 'from'),
    ('^\s*&gt;.*$', 'quote'),
]))

_span = '<span class="%s">%s</span>'


@register.filter
def patchsyntax(patch):
    content = escape(patch.content).replace('\r\n', '\n')

    for (r, cls) in _patch_span_res:
        content = r.sub(lambda x: _span % (cls, x.group(0)), content)

    content = _patch_chunk_re.sub(
        lambda x:
        _span % ('p_chunk', x.group(1)) + ' ' +
        _span % ('p_context', x.group(2)),
        content)

    return mark_safe(content)


@register.filter
def commentsyntax(comment):
    content = escape(comment.content)

    for (r, cls) in _comment_span_res:
        content = r.sub(lambda x: _span % (cls, x.group(0)), content)

    return mark_safe(content)
