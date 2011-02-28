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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from patchwork.requestcontext import PatchworkRequestContext
from django.http import HttpResponse, HttpResponseRedirect
import django.core.urlresolvers
from patchwork.models import Patch, Bundle, BundlePatch, Project
from patchwork.utils import get_patch_ids
from patchwork.forms import BundleForm, DeleteBundleForm
from patchwork.views import generic_list
from patchwork.filters import DelegateFilter

@login_required
def setbundle(request):
    context = PatchworkRequestContext(request)

    bundle = None

    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action is None:
            pass
        elif action == 'create':
            project = get_object_or_404(Project,
                    id = request.POST.get('project'))
            bundle = Bundle(owner = request.user, project = project,
                    name = request.POST['name'])
            bundle.save()
            patch_id = request.POST.get('patch_id', None)
            if patch_id:
                patch = get_object_or_404(Patch, id = patch_id)
                try:
                    bundle.append_patch(patch)
                except Exception:
                    pass
            bundle.save()
        elif action == 'add':
            bundle = get_object_or_404(Bundle,
                    owner = request.user, id = request.POST['id'])
            bundle.save()

            patch_id = request.get('patch_id', None)
            if patch_id:
                patch_ids = patch_id
            else:
                patch_ids = get_patch_ids(request.POST)

            for id in patch_ids:
                try:
                    patch = Patch.objects.get(id = id)
                    bundle.append_patch(patch)
                except:
                    pass

            bundle.save()
        elif action == 'delete':
            try:
                bundle = Bundle.objects.get(owner = request.user,
                        id = request.POST['id'])
                bundle.delete()
            except Exception:
                pass

            bundle = None

    else:
        bundle = get_object_or_404(Bundle, owner = request.user,
                id = request.POST['bundle_id'])

    if 'error' in context:
        pass

    if bundle:
        return HttpResponseRedirect(
                django.core.urlresolvers.reverse(
                    'patchwork.views.bundle.bundle',
                    kwargs = {'bundle_id': bundle.id}
                    )
                )
    else:
        return HttpResponseRedirect(
                django.core.urlresolvers.reverse(
                    'patchwork.views.bundle.list')
                )

@login_required
def bundles(request):
    context = PatchworkRequestContext(request)

    if request.method == 'POST':
        form_name = request.POST.get('form_name', '')

        if form_name == DeleteBundleForm.name:
            form = DeleteBundleForm(request.POST)
            if form.is_valid():
                bundle = get_object_or_404(Bundle,
                    id = form.cleaned_data['bundle_id'])
                bundle.delete()

    bundles = Bundle.objects.filter(owner = request.user)
    for bundle in bundles:
        bundle.delete_form = DeleteBundleForm(auto_id = False,
                initial = {'bundle_id': bundle.id})

    context['bundles'] = bundles

    return render_to_response('patchwork/bundles.html', context)

@login_required
def bundle(request, bundle_id):
    bundle = get_object_or_404(Bundle, id = bundle_id)
    filter_settings = [(DelegateFilter, DelegateFilter.AnyDelegate)]

    if request.method == 'POST' and request.POST.get('form') == 'bundle':
        action = request.POST.get('action', '').lower()
        if action == 'delete':
            bundle.delete()
            return HttpResponseRedirect(
                    django.core.urlresolvers.reverse(
                        'patchwork.views.user.profile')
                    )
        elif action == 'update':
            form = BundleForm(request.POST, instance = bundle)
            if form.is_valid():
                form.save()
    else:
        form = BundleForm(instance = bundle)

    if request.method == 'POST' and request.POST.get('form') == 'reorderform':
        order = get_object_or_404(BundlePatch, bundle = bundle,
                        patch__id = request.POST.get('order_start')).order

        for patch_id in request.POST.getlist('neworder'):
            bundlepatch = get_object_or_404(BundlePatch,
                        bundle = bundle, patch__id = patch_id)
            bundlepatch.order = order
            bundlepatch.save()
            order += 1

    context = generic_list(request, bundle.project,
            'patchwork.views.bundle.bundle',
            view_args = {'bundle_id': bundle_id},
            filter_settings = filter_settings,
            patches = bundle.ordered_patches(),
            editable_order = True)

    context['bundle'] = bundle
    context['bundleform'] = form

    return render_to_response('patchwork/bundle.html', context)

@login_required
def mbox(request, bundle_id):
    bundle = get_object_or_404(Bundle, id = bundle_id)
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=bundle-%d.mbox' % \
        bundle.id
    response.write(bundle.mbox())
    return response

def public(request, username, bundlename):
    user = get_object_or_404(User, username = username)
    bundle = get_object_or_404(Bundle, name = bundlename, owner = user,
                                public = True)
    filter_settings = [(DelegateFilter, DelegateFilter.AnyDelegate)]
    context = generic_list(request, bundle.project,
            'patchwork.views.bundle.public',
            view_args = {'username': username, 'bundlename': bundlename},
            filter_settings = filter_settings,
            patches = bundle.patches.all())

    context['bundle'] = bundle

    return render_to_response('patchwork/bundle-public.html', context)
