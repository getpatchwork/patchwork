# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from patchwork.models import Series
from patchwork.views.utils import series_to_mbox


def series_mbox(request, series_id):
    series = get_object_or_404(Series, id=series_id)

    response = HttpResponse(content_type='text/plain')
    response.write(series_to_mbox(series))
    response['Content-Disposition'] = 'attachment; filename=%s.patch' % (
        series.filename)

    return response
