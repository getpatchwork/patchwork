# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import http
from django.urls import reverse

from patchwork import models


def comment(request, comment_id):
    patch = None
    cover = None

    try:
        patch = models.PatchComment.objects.get(id=comment_id).patch
    except models.PatchComment.DoesNotExist:
        try:
            cover = models.CoverComment.objects.get(id=comment_id).cover
        except models.CoverComment.DoesNotExist:
            pass

    if not patch and not cover:
        raise http.Http404('No comment matches the given query.')

    if patch:
        url = reverse(
            'patch-detail',
            kwargs={
                'project_id': patch.project.linkname,
                'msgid': patch.url_msgid,
            },
        )
    else:  # cover
        url = reverse(
            'cover-detail',
            kwargs={
                'project_id': cover.project.linkname,
                'msgid': cover.url_msgid,
            },
        )

    return http.HttpResponseRedirect('%s#%s' % (url, comment_id))
