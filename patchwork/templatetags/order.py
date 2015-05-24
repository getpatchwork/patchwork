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
import re

register = template.Library()

@register.tag(name = 'ifpatcheditable')
def do_patch_is_editable(parser, token):
    try:
        tag_name, name, cur_order = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments" \
                % token.contents.split()[0])

    end_tag = 'endifpatcheditable'
    nodelist_true = parser.parse([end_tag, 'else'])

    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse([end_tag])
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()

    return EditablePatchNode(patch_var, nodelist_true, nodelist_false)

class EditablePatchNode(template.Node):
    def __init__(self, patch_var, nodelist_true, nodelist_false):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.patch_var = template.Variable(patch_var)
        self.user_var = template.Variable('user')

    def render(self, context):
        try:
            patch = self.patch_var.resolve(context)
            user = self.user_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not user.is_authenticated():
            return self.nodelist_false.render(context)

        if not patch.is_editable(user):
            return self.nodelist_false.render(context)

        return self.nodelist_true.render(context)
