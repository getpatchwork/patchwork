# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django import template
from django.urls import reverse
from django.urls import NoReverseMatch
from django.utils.encoding import smart_str
from django.utils.html import escape

from patchwork.filters import FILTERS


register = template.Library()

# params to preserve across views
list_params = [c.param for c in FILTERS] + ['order', 'page']


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

        path = None
        try:
            path = reverse(view_name, args=[], kwargs=kwargs)
        except NoReverseMatch:
            try:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                path = reverse(project_name + '.' + view_name,
                               args=[], kwargs=kwargs)
            except NoReverseMatch:
                raise

        if path is None:
            return ''

        params = []
        try:
            qs_var = template.Variable('list_view.params').resolve(context)
            params = dict(qs_var)
        except (TypeError, template.VariableDoesNotExist):
            pass

        for (k, v) in self.params.items():
            params[smart_str(k, 'ascii')] = v.resolve(context)

        if not params:
            return path

        return path + '?' + '&'.join(
            ['%s=%s' % (k, escape(v)) for (k, v) in list(params.items())])


@register.tag
def listurl(parser, token):
    bits = token.contents.split(' ', 1)
    if not bits:
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
