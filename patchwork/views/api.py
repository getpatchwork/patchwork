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

import json

from django.db.models import Q
from django.http import HttpResponse

from patchwork.models import Person


def submitters(request):
    search = request.GET.get('q', '')
    limit = request.GET.get('l', None)

    if len(search) <= 3:
        return HttpResponse(content_type="application/json")

    queryset = Person.objects.filter(Q(name__icontains=search) |
                                     Q(email__icontains=search))
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            limit = None

    if limit is not None and limit > 0:
        queryset = queryset[:limit]

    data = []
    for submitter in queryset:
        item = {}
        item['pk'] = submitter.id
        item['name'] = submitter.name
        item['email'] = submitter.email
        data.append(item)

    return HttpResponse(json.dumps(data), content_type="application/json")
