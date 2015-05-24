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

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from patchwork.filters import filterclasses
import re

register = template.Library()

# params to preserve across views
list_params = [ c.param for c in filterclasses ] + ['order', 'page']

class ListURLNode(template.defaulttags.URLNode):
    def __init__(self, *args, **kwargs):
        super(ListURLNode, self).__init__(*args, **kwargs)
        self.params = {}
        for (k, v) in kwargs:
            if k in list_params:
                self.params[k] = v

    def render(self, context):
        self.view_name = template.Variable('list_view.view')
        str = super(ListURLNode, self).render(context)
        if str == '':
            return str
        params = []
        try:
            qs_var = template.Variable('list_view.params')
            params = dict(qs_var.resolve(context))
        except Exception:
            pass

        params.update(self.params)

        if not params:
            return str

        return str + '?' + '&'.join(['%s=%s' % (k, escape(v)) \
                        for (k, v) in params.iteritems()])

@register.tag
def listurl(parser, token):
    bits = token.contents.split(' ', 1)
    if len(bits) < 1:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    args = ['']
    kwargs = {}
    if len(bits) > 1:
        for arg in bits[2].split(','):
            if '=' in arg:
                k, v = arg.split('=', 1)
                k = k.strip()
                kwargs[k] = parser.compile_filter(v)
            else:
                args.append(parser.compile_filter(arg))
    return PatchworkURLNode(bits[1], args, kwargs)

