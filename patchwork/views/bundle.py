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

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.compat import reverse
from patchwork.filters import DelegateFilter
from patchwork.forms import BundleForm
from patchwork.forms import DeleteBundleForm
from patchwork.models import Bundle
from patchwork.models import BundlePatch
from patchwork.models import Project
from patchwork.views import generic_list
from patchwork.views.utils import bundle_to_mbox

if settings.ENABLE_REST_API:
    from rest_framework.authentication import BasicAuthentication  # noqa
    from rest_framework.exceptions import AuthenticationFailed


def rest_auth(request):
    if not settings.ENABLE_REST_API:
        return request.user
    try:
        auth_result = BasicAuthentication().authenticate(request)
        if auth_result:
            return auth_result[0]
    except AuthenticationFailed:
        pass
    return request.user


@login_required
def bundle_list(request, project_id=None):
    project = None

    if request.method == 'POST':
        form_name = request.POST.get('form_name', '')

        if form_name == DeleteBundleForm.name:
            form = DeleteBundleForm(request.POST)
            if form.is_valid():
                bundle = get_object_or_404(Bundle,
                                           id=form.cleaned_data['bundle_id'])
                bundle.delete()

    if project_id is None:
        bundles = Bundle.objects.filter(owner=request.user)
    else:
        project = get_object_or_404(Project, linkname=project_id)
        bundles = Bundle.objects.filter(owner=request.user, project=project)

    for bundle in bundles:
        bundle.delete_form = DeleteBundleForm(auto_id=False,
                                              initial={'bundle_id': bundle.id})

    context = {
        'bundles': bundles,
        'project': project,
    }

    return render(request, 'patchwork/bundles.html', context)


def bundle_detail(request, username, bundlename):
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
                return HttpResponseRedirect(reverse('user-profile'))
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

        if (request.method == 'POST' and
            request.POST.get('form') == 'reorderform'):
            order = get_object_or_404(
                BundlePatch,
                bundle=bundle,
                patch__id=request.POST.get('order_start')).order

            for patch_id in request.POST.getlist('neworder'):
                bundlepatch = get_object_or_404(BundlePatch,
                                                bundle=bundle,
                                                patch__id=patch_id)
                bundlepatch.order = order
                bundlepatch.save()
                order += 1
    else:
        form = None

    context = generic_list(request, bundle.project,
                           'bundle-detail',
                           view_args={'username': bundle.owner.username,
                                      'bundlename': bundle.name},
                           filter_settings=filter_settings,
                           patches=bundle.ordered_patches(),
                           editable_order=is_owner)

    context['bundle'] = bundle
    context['bundleform'] = form

    return render(request, 'patchwork/bundle.html', context)


def bundle_mbox(request, username, bundlename):
    bundle = get_object_or_404(Bundle, owner__username=username,
                               name=bundlename)

    request.user = rest_auth(request)
    if not (request.user == bundle.owner or bundle.public):
        return HttpResponseNotFound()

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = \
        'attachment; filename=bundle-%d-%s.mbox' % (bundle.id, bundle.name)
    response.write(bundle_to_mbox(bundle))

    return response


@login_required
def bundle_detail_redir(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id, owner=request.user)
    return HttpResponseRedirect(bundle.get_absolute_url())


@login_required
def bundle_mbox_redir(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id, owner=request.user)
    return HttpResponseRedirect(
        reverse('bundle-mbox', kwargs={
            'username': request.user.username,
            'bundlename': bundle.name,
        }))
