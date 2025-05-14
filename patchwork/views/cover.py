# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib import messages
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.forms import PatchMaintainerNoteForm
from patchwork.models import Cover, CoverComment
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.views.utils import cover_to_mbox


def cover_detail(request, project_id, msgid):
    project = get_object_or_404(Project, linkname=project_id)
    db_msgid = '<%s>' % msgid

    # redirect to patches where necessary
    try:
        cover = get_object_or_404(Cover, project_id=project.id, msgid=db_msgid)
    except Http404 as exc:
        patches = Patch.objects.filter(
            project_id=project.id,
            msgid=db_msgid,
        )
        if patches:
            return HttpResponseRedirect(
                reverse(
                    'patch-detail',
                    kwargs={'project_id': project.linkname, 'msgid': msgid},
                )
            )
        raise exc

    context = {
        'submission': cover,
        'project': cover.project,
    }

    comments = cover.comments.exclude(msgid='').all()
    comments = comments.select_related('submitter')
    comments = comments.only('submitter', 'date', 'id', 'content', 'cover')
    is_maintainer = (
        request.user.is_superuser
        or request.user.is_authenticated
        and request.user.person_set.all().first()
        and cover.project in request.user.profile.maintainer_projects.all()
    )

    note, create_note_form, edit_note_form, errors = (
        handle_post_maintainer_note(cover, request)
    )

    context['comments'] = comments
    context['note'] = note
    context['is_maintainer'] = is_maintainer
    context['create_note_form'] = create_note_form
    context['edit_note_form'] = edit_note_form
    if errors:
        context['errors'] = errors

    return render(request, 'patchwork/submission.html', context)


def handle_post_maintainer_note(cover, request):
    note = cover.comments.filter(msgid='').all().first()
    create_note_form = None
    edit_note_form = None
    errors = None
    form_name = request.POST.get('form_name', '')
    is_maintainer = (
        request.user.is_superuser
        or request.user.is_authenticated
        and request.user.person_set.all().first()
        and cover.project in request.user.profile.maintainer_projects.all()
    )

    if request.method != 'POST' or not is_maintainer:
        return note, create_note_form, edit_note_form, errors

    if form_name == PatchMaintainerNoteForm.name:
        edit_cancel = bool(request.POST.get('cancel', False))
        if edit_cancel:
            edit_note_form = None
        elif note:
            edit_note_form = PatchMaintainerNoteForm(
                request.POST, instance=note
            )
            if edit_note_form.is_valid():
                note = edit_note_form.save()
                messages.success(request, 'Note updated')
                edit_note_form = None
            else:
                errors = edit_note_form.err

        else:
            create_note = PatchMaintainerNoteForm(
                request.POST,
                instance=CoverComment(
                    cover=cover,
                    submitter=request.user.person_set.all().first(),
                ),
            )
            if create_note.is_valid():
                note = create_note.save()
                messages.success(request, 'Note created')
            else:
                errors = create_note.err
            create_note_form = None

    action = request.POST.get('action', None)
    if action:
        action = action.lower()
    if action == 'note:add':
        create_note_form = PatchMaintainerNoteForm()
    elif action == 'note:edit':
        edit_note_form = PatchMaintainerNoteForm(instance=note)
    elif action == 'note:remove':
        note.delete()
        messages.success(request, 'Note removed')
        note = None

    return note, create_note_form, edit_note_form, errors


def cover_mbox(request, project_id, msgid):
    db_msgid = '<%s>' % msgid
    project = get_object_or_404(Project, linkname=project_id)
    cover = get_object_or_404(Cover, project_id=project.id, msgid=db_msgid)

    response = HttpResponse(content_type='text/plain')
    response.write(cover_to_mbox(cover))
    response['Content-Disposition'] = 'attachment; filename=%s.mbox' % (
        cover.filename
    )

    return response


def cover_by_id(request, cover_id):
    cover = get_object_or_404(Cover, id=cover_id)

    url = reverse(
        'cover-detail',
        kwargs={
            'project_id': cover.project.linkname,
            'msgid': cover.encoded_msgid,
        },
    )

    return HttpResponseRedirect(url)


def cover_mbox_by_id(request, cover_id):
    cover = get_object_or_404(Cover, id=cover_id)

    url = reverse(
        'cover-mbox',
        kwargs={
            'project_id': cover.project.linkname,
            'msgid': cover.encoded_msgid,
        },
    )

    return HttpResponseRedirect(url)
