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


from patchwork.models import Patch, Project, Person, RegistrationRequest, Bundle
from patchwork.filters import Filters
from patchwork.forms import RegisterForm, LoginForm, PatchForm, MultiplePatchForm, CreateBundleForm
from patchwork.utils import get_patch_ids, set_patches, Order
from patchwork.requestcontext import PatchworkRequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, \
	     HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
import django.core.urlresolvers
from patchwork.paginator import Paginator
from patchwork.views import generic_list

def patch(request, patch_id):
    context = PatchworkRequestContext(request)
    patch = get_object_or_404(Patch, id=patch_id)
    context.project = patch.project
    editable = patch.is_editable(request.user)
    messages = []

    form = None
    createbundleform = None

    if editable:
        form = PatchForm(instance = patch)
    if request.user.is_authenticated():
        createbundleform = CreateBundleForm()

    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action:
            action = action.lower()

        if action == 'createbundle':
            bundle = Bundle(owner = request.user, project = patch.project)
            createbundleform = CreateBundleForm(instance = bundle,
                    data = request.POST)
            if createbundleform.is_valid():
                createbundleform.save()
                bundle.patches.add(patch)
                bundle.save()
                createbundleform = CreateBundleForm()
                context.add_message('Bundle %s created' % bundle.name)

        elif action == 'addtobundle':
            bundle = get_object_or_404(Bundle, id = \
                        request.POST.get('bundle_id'))
            bundle.patches.add(patch)
            bundle.save()
            context.add_message('Patch added to bundle "%s"' % bundle.name)

	# all other actions require edit privs
        elif not editable:
            return HttpResponseForbidden()

        elif action is None:
            form = PatchForm(data = request.POST, instance = patch)
            if form.is_valid():
                form.save()
                context.add_message('Patch updated')

	elif action == 'archive':
	    patch.archived = True
	    patch.save()
            context.add_message('Patch archived')

	elif action == 'unarchive':
	    patch.archived = False
	    patch.save()
            context.add_message('Patch un-archived')

        elif action == 'ack':
            pass

        elif action == 'delete':
            patch.delete()


    context['patch'] = patch
    context['patchform'] = form
    context['createbundleform'] = createbundleform
    context['project'] = patch.project

    return render_to_response('patchwork/patch.html', context)

def content(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)
    response = HttpResponse(mimetype="text/x-patch")
    response.write(patch.content)
    response['Content-Disposition'] = 'attachment; filename=' + \
        patch.filename().replace(';', '').replace('\n', '')
    return response

def mbox(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)
    response = HttpResponse(mimetype="text/plain")
    response.write(patch.mbox().as_string(True))
    response['Content-Disposition'] = 'attachment; filename=' + \
        patch.filename().replace(';', '').replace('\n', '')
    return response


def list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    context = generic_list(request, project, 'patchwork.views.patch.list',
            view_args = {'project_id': project.linkname})
    return render_to_response('patchwork/list.html', context)

    context = PatchworkRequestContext(request,
            list_view = 'patchwork.views.patch.list',
            list_view_params = {'project_id': project_id})
    order = get_order(request)
    project = get_object_or_404(Project, linkname=project_id)
    context.project = project

    form = None
    errors = []

    if request.method == 'POST':
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
				request.POST, ps)
        if errors:
            context['errors'] = errors


    elif request.user.is_authenticated() and \
	    project in request.user.get_profile().maintainer_projects.all():
        form = MultiplePatchForm(project)

    patches = Patch.objects.filter(project=project).order_by(order)
    patches = context.filters.apply(patches)

    paginator = Paginator(request, patches)

    context.update({
            'page':             paginator.current_page,
            'patchform':        form,
            'project':          project,
            'errors':           errors,
            })

    return render_to_response('patchwork/list.html', context)
