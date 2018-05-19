# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.models import CoverLetter
from patchwork.models import Submission
from patchwork.views.utils import cover_to_mbox


def cover_detail(request, cover_id):
    # redirect to patches where necessary
    try:
        cover = get_object_or_404(CoverLetter, id=cover_id)
    except Http404 as exc:
        submissions = Submission.objects.filter(id=cover_id)
        if submissions:
            return HttpResponseRedirect(
                reverse('patch-detail', kwargs={'patch_id': cover_id}))
        raise exc

    context = {
        'submission': cover,
        'project': cover.project,
    }

    comments = cover.comments.all()
    comments = comments.select_related('submitter')
    comments = comments.only('submitter', 'date', 'id', 'content',
                             'submission')
    context['comments'] = comments

    return render(request, 'patchwork/submission.html', context)


def cover_mbox(request, cover_id):
    cover = get_object_or_404(CoverLetter, id=cover_id)

    response = HttpResponse(content_type='text/plain')
    response.write(cover_to_mbox(cover))
    response['Content-Disposition'] = 'attachment; filename=%s.mbox' % (
        cover.filename)

    return response
