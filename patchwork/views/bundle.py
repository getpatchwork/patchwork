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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import django.core.urlresolvers
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404

from patchwork.filters import DelegateFilter
from patchwork.forms import BundleForm, DeleteBundleForm
from patchwork.models import Patch, Bundle, BundlePatch, Project
from patchwork.requestcontext import PatchworkRequestContext
from patchwork.utils import get_patch_ids
from patchwork.views import generic_list, patch_to_mbox


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
                                        id=request.POST.get('project'))
            bundle = Bundle(owner=request.user, project=project,
                            name=request.POST['name'])
            bundle.save()
            patch_id = request.POST.get('patch_id', None)
            if patch_id:
                patch = get_object_or_404(Patch, id=patch_id)
                try:
                    bundle.append_patch(patch)
                except Exception:
                    pass
            bundle.save()
        elif action == 'add':
            bundle = get_object_or_404(Bundle,
                                       owner=request.user, id=request.POST['id'])
            bundle.save()

            patch_id = request.get('patch_id', None)
            if patch_id:
                patch_ids = patch_id
            else:
                patch_ids = get_patch_ids(request.POST)

            for id in patch_ids:
                try:
                    patch = Patch.objects.get(id=id)
                    bundle.append_patch(patch)
                except:
                    pass

            bundle.save()
        elif action == 'delete':
            try:
                bundle = Bundle.objects.get(owner=request.user,
                                            id=request.POST['id'])
                bundle.delete()
            except Exception:
                pass

            bundle = None

    else:
        bundle = get_object_or_404(Bundle, owner=request.user,
                                   id=request.POST['bundle_id'])

    if 'error' in context:
        pass

    if bundle:
        return HttpResponseRedirect(
            django.core.urlresolvers.reverse(
                'patchwork.views.bundle.bundle',
                kwargs={'bundle_id': bundle.id}
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
                                           id=form.cleaned_data['bundle_id'])
                bundle.delete()

    bundles = Bundle.objects.filter(owner=request.user)
    for bundle in bundles:
        bundle.delete_form = DeleteBundleForm(auto_id=False,
                                              initial={'bundle_id': bundle.id})

    context['bundles'] = bundles

    return render_to_response('patchwork/bundles.html', context)


def bundle(request, username, bundlename):
    bundle = get_object_or_404(Bundle, owner__username=username,
                               name=bundlename)
    filter_settings = [(DelegateFilter, DelegateFilter.AnyDelegate)]

    is_owner = request.user == bundle.owner

    if not (is_owner or bundle.public):
        return HttpResponseNotFound()

    if is_owner:
        if request.method == 'POST' and request.POST.get('form') == 'bundle':
            action = request.POST.get('action', '').lower()
            if action == 'delete':
                bundle.delete()
                return HttpResponseRedirect(
                    django.core.urlresolvers.reverse(
                        'patchwork.views.user.profile')
                )
            elif action == 'update':
                form = BundleForm(request.POST, instance=bundle)
                if form.is_valid():
                    form.save()

                # if we've changed the bundle name, redirect to new URL
                bundle = Bundle.objects.get(pk=bundle.pk)
                if bundle.name != bundlename:
                    return HttpResponseRedirect(bundle.get_absolute_url())

            else:
                form = BundleForm(instance=bundle)
        else:
            form = BundleForm(instance=bundle)

        if request.method == 'POST' and \
                request.POST.get('form') == 'reorderform':
            order = get_object_or_404(BundlePatch, bundle=bundle,
                                      patch__id=request.POST.get('order_start')).order

            for patch_id in request.POST.getlist('neworder'):
                bundlepatch = get_object_or_404(BundlePatch,
                                                bundle=bundle, patch__id=patch_id)
                bundlepatch.order = order
                bundlepatch.save()
                order += 1
    else:
        form = None

    context = generic_list(request, bundle.project,
                           'patchwork.views.bundle.bundle',
                           view_args={'username': bundle.owner.username,
                                      'bundlename': bundle.name},
                           filter_settings=filter_settings,
                           patches=bundle.ordered_patches(),
                           editable_order=is_owner)

    context['bundle'] = bundle
    context['bundleform'] = form

    return render_to_response('patchwork/bundle.html', context)


def mbox(request, username, bundlename):
    bundle = get_object_or_404(Bundle, owner__username=username,
                               name=bundlename)

    if not (request.user == bundle.owner or bundle.public):
        return HttpResponseNotFound()

    mbox = '\n'.join([patch_to_mbox(p).as_string(True)
                      for p in bundle.ordered_patches()])

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = \
        'attachment; filename=bundle-%d-%s.mbox' % (bundle.id, bundle.name)

    response.write(mbox)
    return response


@login_required
def bundle_redir(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id, owner=request.user)
    return HttpResponseRedirect(bundle.get_absolute_url())


@login_required
def mbox_redir(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id, owner=request.user)
    return HttpResponseRedirect(django.core.urlresolvers.reverse(
                                'patchwork.views.bundle.mbox', kwargs={
                                    'username': request.user.username,
                                    'bundlename': bundle.name,
                                }))
