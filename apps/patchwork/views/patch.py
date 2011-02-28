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


from patchwork.models import Patch, Project, Bundle
from patchwork.forms import PatchForm, CreateBundleForm
from patchwork.requestcontext import PatchworkRequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from patchwork.views import generic_list

def patch(request, patch_id):
    context = PatchworkRequestContext(request)
    patch = get_object_or_404(Patch, id=patch_id)
    context.project = patch.project
    editable = patch.is_editable(request.user)

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
                bundle.append_patch(patch)
                bundle.save()
                createbundleform = CreateBundleForm()
                context.add_message('Bundle %s created' % bundle.name)

        elif action == 'addtobundle':
            bundle = get_object_or_404(Bundle, id = \
                        request.POST.get('bundle_id'))
            try:
                bundle.append_patch(patch)
                bundle.save()
                context.add_message('Patch added to bundle "%s"' % bundle.name)
            except Exception, ex:
                context.add_message("Couldn't add patch '%s' to bundle %s: %s" \
                        % (patch.name, bundle.name, ex.message))

        # all other actions require edit privs
        elif not editable:
            return HttpResponseForbidden()

        elif action is None:
            form = PatchForm(data = request.POST, instance = patch)
            if form.is_valid():
                form.save()
                context.add_message('Patch updated')

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
