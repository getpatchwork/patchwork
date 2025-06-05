# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib import messages
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.forms import CreateBundleForm
from patchwork.forms import PatchMaintainerNoteForm
from patchwork.forms import PatchForm
from patchwork.models import Cover
from patchwork.models import PatchComment
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.views import generic_list
from patchwork.views import set_bundle
from patchwork.views.utils import patch_to_mbox
from patchwork.views.utils import series_patch_to_mbox


def patch_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    context = generic_list(
        request,
        project,
        'patch-list',
        view_args={'project_id': project.linkname},
    )

    if request.user.is_authenticated:
        context['bundles'] = request.user.bundles.all()

    return render(request, 'patchwork/list.html', context)


def patch_detail(request, project_id, msgid):
    project = get_object_or_404(Project, linkname=project_id)
    db_msgid = Patch.decode_msgid(msgid)

    # redirect to cover letters where necessary
    try:
        patch = Patch.objects.get(project_id=project.id, msgid=db_msgid)
    except Patch.DoesNotExist:
        covers = Cover.objects.filter(
            project_id=project.id,
            msgid=db_msgid,
        )
        if covers:
            return HttpResponseRedirect(
                reverse(
                    'cover-detail',
                    kwargs={'project_id': project.linkname, 'msgid': msgid},
                )
            )
        raise Http404('Patch does not exist')

    editable = patch.is_editable(request.user)
    context = {'project': patch.project}

    note = patch.comments.filter(msgid='').all().first()
    form = None
    create_bundle_form = None
    create_note_form = None
    edit_note_form = None
    errors = None
    is_maintainer = (
        request.user.is_superuser
        or request.user.is_authenticated
        and request.user.person_set.all().first()
        and patch.project in request.user.profile.maintainer_projects.all()
    )

    if editable:
        form = PatchForm(instance=patch)
    if request.user.is_authenticated:
        create_bundle_form = CreateBundleForm()

    if request.method == 'POST':
        form_name = request.POST.get('form_name', '')
        if is_maintainer and form_name == PatchMaintainerNoteForm.name:
            edit_cancel = bool(request.POST.get('cancel', False))
            if edit_cancel:
                edit_note_form = None
            elif note:
                edit_note_form = PatchMaintainerNoteForm(
                    request.POST, instance=note
                )
                if edit_note_form.is_valid():
                    edit_note_form.save()
                    messages.success(request, 'Note updated')
                    edit_note_form = None
                else:
                    errors = edit_note_form.err

            else:
                create_note = PatchMaintainerNoteForm(
                    request.POST,
                    instance=PatchComment(
                        patch=patch,
                        submitter=request.user.person_set.all().first(),
                    ),
                )
                if create_note.is_valid():
                    note = create_note.save()
                    messages.success(request, 'Note created')
                else:
                    errors = create_note.err
                create_note_form = None

        else:
            action = request.POST.get('action', None)
            if action:
                action = action.lower()

            if is_maintainer and action == 'note:add':
                create_note_form = PatchMaintainerNoteForm()
            elif is_maintainer and action == 'note:edit':
                edit_note_form = PatchMaintainerNoteForm(instance=note)
            elif is_maintainer and action == 'note:remove':
                note.delete()
                messages.success(request, 'Note removed')
                note = None

            elif action in ['create', 'add']:
                errors = set_bundle(
                    request, project, action, request.POST, [patch]
                )

            elif not editable:
                return HttpResponseForbidden()

            elif action == 'update':
                form = PatchForm(data=request.POST, instance=patch)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Patch updated')

    if request.user.is_authenticated:
        context['bundles'] = request.user.bundles.all()

    comments = patch.comments.exclude(msgid='').all()
    comments = comments.select_related('submitter')
    comments = comments.only(
        'submitter', 'date', 'id', 'content', 'patch', 'addressed'
    )

    if patch.related:
        related_same_project = patch.related.patches.only(
            'name', 'msgid', 'project', 'related'
        )
        # avoid a second trip out to the db for info we already have
        related_different_project = [
            related_patch
            for related_patch in related_same_project
            if related_patch.project_id != patch.project_id
        ]
    else:
        related_same_project = []
        related_different_project = []

    if is_maintainer:
        context['note'] = note

    context['comments'] = comments
    context['checks'] = Patch.filter_unique_checks(
        patch.check_set.all().select_related('user'),
    )
    context['submission'] = patch
    context['editable'] = editable
    context['is_maintainer'] = is_maintainer
    context['create_note_form'] = create_note_form
    context['edit_note_form'] = edit_note_form
    context['patch_form'] = form
    context['create_bundle_form'] = create_bundle_form
    context['project'] = patch.project
    context['related_same_project'] = related_same_project
    context['related_different_project'] = related_different_project
    if errors:
        context['errors'] = errors

    return render(request, 'patchwork/submission.html', context)


def patch_raw(request, project_id, msgid):
    db_msgid = Patch.decode_msgid(msgid)
    project = get_object_or_404(Project, linkname=project_id)
    patch = get_object_or_404(Patch, project_id=project.id, msgid=db_msgid)

    response = HttpResponse(content_type='text/x-patch')
    response.write(patch.diff)
    response['Content-Disposition'] = 'attachment; filename=%s.diff' % (
        patch.filename
    )

    return response


def patch_mbox(request, project_id, msgid):
    db_msgid = Patch.decode_msgid(msgid)
    project = get_object_or_404(Project, linkname=project_id)
    patch = get_object_or_404(Patch, project_id=project.id, msgid=db_msgid)
    series_id = request.GET.get('series')

    response = HttpResponse(content_type='text/plain; charset=utf-8')
    if series_id:
        response.write(series_patch_to_mbox(patch, series_id))
    else:
        response.write(patch_to_mbox(patch))
    response['Content-Disposition'] = 'attachment; filename=%s.patch' % (
        patch.filename
    )

    return response


def patch_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse(
        'patch-detail',
        kwargs={
            'project_id': patch.project.linkname,
            'msgid': patch.encoded_msgid,
        },
    )

    return HttpResponseRedirect(url)


def patch_mbox_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse(
        'patch-mbox',
        kwargs={
            'project_id': patch.project.linkname,
            'msgid': patch.encoded_msgid,
        },
    )

    return HttpResponseRedirect(url)


def patch_raw_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse(
        'patch-raw',
        kwargs={
            'project_id': patch.project.linkname,
            'msgid': patch.encoded_msgid,
        },
    )

    return HttpResponseRedirect(url)
