# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
