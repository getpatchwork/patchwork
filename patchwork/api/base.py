# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import rest_framework

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.serializers import HyperlinkedIdentityField
from rest_framework.serializers import HyperlinkedModelSerializer

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
                self.lookup_fields, self.lookup_url_kwargs):
            if self.kwargs[field]:
                filter_kwargs[field_name] = self.kwargs[field]

        return get_object_or_404(queryset, **filter_kwargs)


class CheckHyperlinkedIdentityField(HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        return self.reverse(
            view_name,
            kwargs={
                'patch_id': obj.patch.id,
                'check_id': obj.id,
            },
            request=request,
            format=format,
        )


class BaseHyperlinkedModelSerializer(HyperlinkedModelSerializer):

    def to_representation(self, instance):
        data = super(BaseHyperlinkedModelSerializer, self).to_representation(
            instance)

        request = self.context.get('request')
        for version in getattr(self.Meta, 'versioned_fields', {}):
            # if the user has requested a version lower that than in which the
            # field was added, we drop it
            if not utils.has_version(request, version):
                for field in self.Meta.versioned_fields[version]:
                    # After a PATCH with an older API version, we may not see
                    # these fields. If they don't exist, don't panic, return
                    # (and then discard) None.
                    data.pop(field, None)

        return data
