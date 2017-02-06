# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from patchwork.models import Series
from patchwork.views.utils import series_to_mbox


def series_mbox(request, series_id):
    series = get_object_or_404(Series, id=series_id)

    response = HttpResponse(content_type='text/plain')
    response.write(series_to_mbox(series))
    response['Content-Disposition'] = 'attachment; filename=' + \
        series.filename.replace(';', '').replace('\n', '')

    return response
