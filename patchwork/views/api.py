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
from patchwork.models import User


MINIMUM_CHARACTERS = 3


def _handle_request(request, queryset_fn, formatter):
    search = request.GET.get('q', '')
    limit = request.GET.get('l', None)

    if len(search) < MINIMUM_CHARACTERS:
        return HttpResponse(content_type='application/json')

    queryset = queryset_fn(search)
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            limit = None

    if limit is not None and limit > 0:
        queryset = queryset[:limit]

    data = []
    for item in queryset:
        data.append(formatter(item))

    return HttpResponse(json.dumps(data), content_type='application/json')


def submitters(request):
    def queryset(search):
        return Person.objects.filter(Q(name__icontains=search) |
                                     Q(email__icontains=search))

    def formatter(submitter):
        return {
            'pk': submitter.id,
            'name': submitter.name,
            'email': submitter.email,
        }

    return _handle_request(request, queryset, formatter)


def delegates(request):
    def queryset(search):
        return User.objects.filter(Q(username__icontains=search) |
                                   Q(first_name__icontains=search) |
                                   Q(last_name__icontains=search))

    def formatter(user):
        return {
            'pk': user.id,
            'name': str(user),
        }

    return _handle_request(request, queryset, formatter)
