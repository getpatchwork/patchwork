# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
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

from django.core import urlresolvers
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from patchwork.models import CoverLetter
from patchwork.models import Submission


def cover_detail(request, cover_id):
    # redirect to patches where necessary
    try:
        cover = get_object_or_404(CoverLetter, id=cover_id)
    except Http404 as exc:
        submissions = Submission.objects.filter(id=cover_id)
        if submissions:
            return HttpResponseRedirect(
                urlresolvers.reverse(
                    'patch-detail',
                    kwargs={'patch_id': cover_id}))
        raise exc

    context = {
        'submission': cover,
        'project': cover.project,
    }

    return render_to_response('patchwork/submission.html', context)
