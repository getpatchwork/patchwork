# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LinkHeaderPagination(PageNumberPagination):
    """Provide pagination based on rfc5988.

    This is the Link header, similar to how GitHub does it. See:

       https://tools.ietf.org/html/rfc5988#section-5
       https://developer.github.com/guides/traversing-with-pagination
    """
    page_size = settings.REST_RESULTS_PER_PAGE
    page_size_query_param = 'per_page'

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        link = ''
        if next_url is not None and previous_url is not None:
            link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            link = '<{next_url}>; rel="next"'
        elif previous_url is not None:
            link = '<{previous_url}>; rel="prev"'
        link = link.format(next_url=next_url, previous_url=previous_url)
        headers = {'Link': link} if link else {}
        return Response(data, headers=headers)


class PatchworkPermission(permissions.BasePermission):
    """This permission works for Project and Patch model objects"""
    def has_object_permission(self, request, view, obj):
        # read only for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.is_editable(request.user)


class MultipleFieldLookupMixin(object):
    """Enable multiple lookups fields."""

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {}
        for field_name, field in zip(
                self.lookup_fields, self.lookup_url_kwargs):
            if self.kwargs[field]:
                filter_kwargs[field_name] = self.kwargs[field]

        return get_object_or_404(queryset, **filter_kwargs)
