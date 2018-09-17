# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import http
from django import shortcuts
from django.urls import reverse

from patchwork import models


def comment(request, comment_id):
    submission = shortcuts.get_object_or_404(models.Comment,
                                             id=comment_id).submission
    if models.Patch.objects.filter(id=submission.id).exists():
        url = 'patch-detail'
        key = 'patch_id'
    else:
        url = 'cover-detail'
        key = 'cover_id'

    return http.HttpResponseRedirect('%s#%s' % (
        reverse(url, kwargs={key: submission.id}), comment_id))
