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


from patchwork.forms import MultiplePatchForm
from patchwork.models import Bundle, Project, State, UserProfile
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404

def get_patch_ids(d, prefix = 'patch_id'):
    ids = []

    for (k, v) in d.items():
        a = k.split(':')
        if len(a) != 2:
            continue
        if a[0] != prefix:
            continue
        if not v:
            continue
        ids.append(a[1])

    return ids

class Order(object):
    order_map = {
        'date':         'date',
        'name':         'name',
        'state':        'state__ordering',
        'submitter':    'submitter__name',
        'delegate':     'delegate__username',
    }
    default_order = ('date', True)

    def __init__(self, str = None, editable = False):
        self.reversed = False
        self.editable = editable

        if self.editable:
            return

        if str is None or str == '':
            (self.order, self.reversed) = self.default_order
            return

        reversed = False
        if str[0] == '-':
            str = str[1:]
            reversed = True

        if str not in self.order_map.keys():
            (self.order, self.reversed) = self.default_order
            return

        self.order = str
        self.reversed = reversed

    def __str__(self):
        str = self.order
        if self.reversed:
            str = '-' + str
        return str

    def name(self):
        return self.order

    def reversed_name(self):
        if self.reversed:
            return self.order
        else:
            return '-' + self.order

    def query(self):
        q = self.order_map[self.order]
        if self.reversed:
            q = '-' + q
        return q

bundle_actions = ['create', 'add', 'remove']
def set_bundle(user, project, action, data, patches, context):
    # set up the bundle
    bundle = None
    if action == 'create':
        bundle = Bundle(owner = user, project = project,
                name = data['bundle_name'])
        bundle.save()
        str = 'added to new bundle "%s"' % bundle.name
        auth_required = False

    elif action =='add':
        bundle = get_object_or_404(Bundle, id = data['bundle_id'])
        str = 'added to bundle "%s"' % bundle.name
        auth_required = False

    elif action =='remove':
        bundle = get_object_or_404(Bundle, id = data['removed_bundle_id'])
        str = 'removed from bundle "%s"' % bundle.name
        auth_required = False

    if not bundle:
        return ['no such bundle']

    for patch in patches:
        if action == 'create' or action == 'add':
            bundle.append_patch(patch)

        elif action == 'remove':
            bundle.patches.remove(patch)

    if len(patches) > 0:
        if len(patches) == 1:
            str = 'patch ' + str
        else:
            str = 'patches ' + str
        context.add_message(str)

    bundle.save()

    return []


def set_patches(user, project, action, data, patches, context):
    errors = []
    form = MultiplePatchForm(project = project, data = data)

    try:
        project = Project.objects.get(id = data['project'])
    except:
        errors = ['No such project']
        return (errors, form)

    str = ''

    # this may be a bundle action, which doesn't modify a patch. in this
    # case, don't require a valid form, or patch editing permissions
    if action in bundle_actions:
        errors = set_bundle(user, project, action, data, patches, context)
        return (errors, form)

    if not form.is_valid():
        errors = ['The submitted form data was invalid']
        return (errors, form)

    for patch in patches:
        if not patch.is_editable(user):
            errors.append('You don\'t have permissions to edit the ' + \
                    'patch "%s"' \
                    % patch.name)
            continue

        if action == 'update':
            form.save(patch)
            str = 'updated'

        elif action == 'ack':
            pass

        elif action == 'archive':
            patch.archived = True
            patch.save()
            str = 'archived'

        elif action == 'unarchive':
            patch.archived = True
            patch.save()
            str = 'un-archived'

        elif action == 'delete':
            patch.delete()
            str = 'un-archived'


    if len(patches) > 0:
        if len(patches) == 1:
            str = 'patch ' + str
        else:
            str = 'patches ' + str
        context.add_message(str)

    return (errors, form)

def userprofile_register_callback(user):
    profile = UserProfile(user = user)
    profile.save()

