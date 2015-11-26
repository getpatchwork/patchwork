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

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django import template
from django.utils.encoding import smart_str
from django.utils.html import escape

from patchwork.filters import filterclasses


register = template.Library()

# params to preserve across views
list_params = [c.param for c in filterclasses] + ['order', 'page']


class ListURLNode(template.defaulttags.URLNode):

    def __init__(self, kwargs):
        super(ListURLNode, self).__init__(None, [], {}, False)
        self.params = {}
        for (k, v) in kwargs.items():
            if k in list_params:
                self.params[k] = v

    def render(self, context):
        view_name = template.Variable('list_view.view').resolve(context)
        kwargs = template.Variable('list_view.view_params').resolve(context)

        str = None
        try:
            str = reverse(view_name, args=[], kwargs=kwargs)
        except NoReverseMatch:
            try:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                str = reverse(project_name + '.' + view_name,
                              args=[], kwargs=kwargs)
            except NoReverseMatch:
                raise

        if str is None:
            return ''

        params = []
        try:
            qs_var = template.Variable('list_view.params')
            params = dict(qs_var.resolve(context))
        except Exception:
            pass

        for (k, v) in self.params.items():
            params[smart_str(k, 'ascii')] = v.resolve(context)

        if not params:
            return str

        return str + '?' + '&'.join(
            ['%s=%s' % (k, escape(v)) for (k, v) in list(params.items())])


@register.tag
def listurl(parser, token):
    bits = token.contents.split(' ', 1)
    if len(bits) < 1:
        raise template.TemplateSyntaxError(
            "'%s' takes at least one argument (path to a view)" % bits[0])
    kwargs = {}
    if len(bits) > 1:
        for arg in bits[1].split(','):
            if '=' in arg:
                k, v = arg.split('=', 1)
                k = k.strip()
                kwargs[k] = parser.compile_filter(v)
            else:
                raise template.TemplateSyntaxError(
                    "'%s' requires name=value params" % bits[0])
    return ListURLNode(kwargs)
