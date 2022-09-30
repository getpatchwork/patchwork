# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import rest_framework

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.response import Response
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.utils.urls import replace_query_param

from patchwork.api import utils


DRF_VERSION = tuple(int(x) for x in rest_framework.__version__.split('.'))


if DRF_VERSION > (3, 11):

    class CurrentPatchDefault(object):
        requires_context = True

        def __call__(self, serializer_field):
            return serializer_field.context['request'].patch

    class CurrentCoverDefault(object):
        requires_context = True

        def __call__(self, serializer_field):
            return serializer_field.context['request'].cover

else:

    class CurrentPatchDefault(object):
        def set_context(self, serializer_field):
            self.patch = serializer_field.context['request'].patch

        def __call__(self):
            return self.patch

    class CurrentCoverDefault(object):
        def set_context(self, serializer_field):
            self.patch = serializer_field.context['request'].cover

        def __call__(self):
            return self.cover


class LinkHeaderPagination(PageNumberPagination):
    """Provide pagination based on rfc5988.

    This is the Link header, similar to how GitHub does it. See:

       https://tools.ietf.org/html/rfc5988#section-5
       https://developer.github.com/guides/traversing-with-pagination
    """

    page_size = settings.REST_RESULTS_PER_PAGE
    max_page_size = settings.MAX_REST_RESULTS_PER_PAGE
    page_size_query_param = 'per_page'

    def get_first_link(self):
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self):
        url = self.request.build_absolute_uri()
        page_number = self.page.paginator.num_pages
        return replace_query_param(url, self.page_query_param, page_number)

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()
        first_url = self.get_first_link()
        last_url = self.get_last_link()

        links = []

        if next_url is not None:
            links.append(f'<{next_url}>; rel="next"')

        if previous_url is not None:
            links.append(f'<{previous_url}>; rel="prev"')

        links.append(f'<{first_url}>; rel="first"')
        links.append(f'<{last_url}>; rel="last"')

        headers = {'Link': ', '.join(links)} if links else {}
        return Response(data, headers=headers)


class PatchworkPermission(permissions.BasePermission):
    """
    This permission works for Project, Patch, PatchComment
    and CoverComment model objects
    """

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
            self.lookup_fields, self.lookup_url_kwargs
        ):
            if self.kwargs[field]:
                filter_kwargs[field_name] = self.kwargs[field]

        return get_object_or_404(queryset, **filter_kwargs)


class NestedHyperlinkedIdentityField(HyperlinkedIdentityField):
    """A variant of HyperlinkedIdentityField that supports nested resources."""

    def __init__(self, view_name, lookup_field_mapping, **kwargs):
        self.lookup_field_mapping = lookup_field_mapping
        super().__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        kwargs = {}
        for (
            lookup_url_kwarg,
            lookup_field,
        ) in self.lookup_field_mapping.items():
            kwargs[lookup_url_kwarg] = getattr(obj, lookup_field)

        return self.reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format,
        )


class BaseHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    def to_representation(self, instance):
        request = self.context.get('request')
        for version in getattr(self.Meta, 'versioned_fields', {}):
            # if the user has requested a version lower that than in which the
            # field was added, we drop it
            if not utils.has_version(request, version):
                for field in self.Meta.versioned_fields[version]:
                    if field in self.fields:
                        del self.fields[field]

        data = super(BaseHyperlinkedModelSerializer, self).to_representation(
            instance
        )

        return data
