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


from base import *
from patchwork.utils import Order, get_patch_ids, set_patches
from patchwork.paginator import Paginator
from patchwork.forms import MultiplePatchForm

def generic_list(request, project, view,
        view_args = {}, filter_settings = [], patches = None,
        editable_order = False):

    context = PatchworkRequestContext(request,
            list_view = view,
            list_view_params = view_args)

    context.project = project
    order = Order(request.REQUEST.get('order'), editable = editable_order)

    form = MultiplePatchForm(project)

    if request.method == 'POST' and \
                       request.POST.get('form') == 'patchlistform':
        action = request.POST.get('action', None)
        if action:
            action = action.lower()

        # special case: the user may have hit enter in the 'create bundle'
        # text field, so if non-empty, assume the create action:
        if request.POST.get('bundle_name', False):
            action = 'create'

        ps = []
        for patch_id in get_patch_ids(request.POST):
            try:
                patch = Patch.objects.get(id = patch_id)
            except Patch.DoesNotExist:
                pass
            ps.append(patch)

        (errors, form) = set_patches(request.user, project, action, \
                request.POST, ps, context)
        if errors:
            context['errors'] = errors

    if not (request.user.is_authenticated() and \
            project in request.user.get_profile().maintainer_projects.all()):
        form = None

    for (filterclass, setting) in filter_settings:
        if isinstance(setting, dict):
            context.filters.set_status(filterclass, **setting)
        elif isinstance(setting, list):
            context.filters.set_status(filterclass, *setting)
        else:
            context.filters.set_status(filterclass, setting)

    if patches is None:
        patches = Patch.objects.filter(project=project)

    patches = context.filters.apply(patches)
    if not editable_order:
        patches = patches.order_by(order.query())

    paginator = Paginator(request, patches)

    context.update({
            'page':             paginator.current_page,
            'patchform':        form,
            'project':          project,
            'order':            order,
            })

    return context

