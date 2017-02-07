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

from django.contrib import messages
from django.core import urlresolvers
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from patchwork.forms import PatchForm, CreateBundleForm
from patchwork.models import Patch, Project, Bundle, Submission
from patchwork.views import generic_list
from patchwork.views.utils import patch_to_mbox


def patch_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    context = generic_list(request, project, 'patch-list',
                           view_args={'project_id': project.linkname})
    return render(request, 'patchwork/list.html', context)


def patch_detail(request, patch_id):
    # redirect to cover letters where necessary
    try:
        patch = get_object_or_404(Patch, id=patch_id)
    except Http404 as exc:
        submissions = Submission.objects.filter(id=patch_id)
        if submissions:
            return HttpResponseRedirect(
                urlresolvers.reverse(
                    'cover-detail',
                    kwargs={'cover_id': patch_id}))
        raise exc

    editable = patch.is_editable(request.user)
    context = {
        'project': patch.project
    }

    form = None
    createbundleform = None

    if editable:
        form = PatchForm(instance=patch)
    if request.user.is_authenticated():
        createbundleform = CreateBundleForm()

    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action:
            action = action.lower()

        if action == 'createbundle':
            bundle = Bundle(owner=request.user, project=patch.project)
            createbundleform = CreateBundleForm(instance=bundle,
                                                data=request.POST)
            if createbundleform.is_valid():
                createbundleform.save()
                bundle.append_patch(patch)
                bundle.save()
                createbundleform = CreateBundleForm()
                messages.success(request, 'Bundle %s created' % bundle.name)
        elif action == 'addtobundle':
            bundle = get_object_or_404(
                Bundle, id=request.POST.get('bundle_id'))
            if bundle.append_patch(patch):
                messages.success(request,
                                 'Patch "%s" added to bundle "%s"' % (
                                     patch.name, bundle.name))
            else:
                messages.error(request,
                               'Failed to add patch "%s" to bundle "%s": '
                               'patch is already in bundle' % (
                                   patch.name, bundle.name))

        # all other actions require edit privs
        elif not editable:
            return HttpResponseForbidden()

        elif action is None:
            form = PatchForm(data=request.POST, instance=patch)
            if form.is_valid():
                form.save()
                messages.success(request, 'Patch updated')

    if request.user.is_authenticated():
        context['bundles'] = Bundle.objects.filter(owner=request.user)

    context['submission'] = patch
    context['patchform'] = form
    context['createbundleform'] = createbundleform
    context['project'] = patch.project

    return render(request, 'patchwork/submission.html', context)


def patch_raw(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)
    response = HttpResponse(content_type="text/x-patch")
    response.write(patch.diff)
    response['Content-Disposition'] = 'attachment; filename=' + \
        patch.filename.replace(';', '').replace('\n', '')

    return response


def patch_mbox(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)
    response = HttpResponse(content_type="text/plain")
    response.write(patch_to_mbox(patch))
    response['Content-Disposition'] = 'attachment; filename=' + \
        patch.filename.replace(';', '').replace('\n', '')

    return response
