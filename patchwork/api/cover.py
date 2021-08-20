# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.reverse import reverse
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.filters import CoverFilterSet
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.models import Cover


class CoverListSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    submitter = PersonSerializer(read_only=True)
    mbox = SerializerMethodField()
    series = SeriesSerializer(read_only=True)
    comments = SerializerMethodField()

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def get_comments(self, cover):
        return self.context.get('request').build_absolute_uri(
            reverse('api-cover-comment-list', kwargs={'cover_id': cover.id}))

    def to_representation(self, instance):
        # NOTE(stephenfin): This is here to ensure our API looks the same even
        # after we changed the series-patch relationship from M:N to 1:N. It
        # will be removed in API v2
        data = super(CoverListSerializer, self).to_representation(
            instance)
        data['series'] = [data['series']] if data['series'] else []
        return data

    class Meta:
        model = Cover
        fields = ('id', 'url', 'web_url', 'project', 'msgid',
                  'list_archive_url', 'date', 'name', 'submitter', 'mbox',
                  'series', 'comments')
        read_only_fields = fields
        versioned_fields = {
            '1.1': ('web_url', 'mbox', 'comments'),
            '1.2': ('list_archive_url',),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-cover-detail'},
        }


class CoverDetailSerializer(CoverListSerializer):

    headers = SerializerMethodField()

    def get_headers(self, instance):
        headers = {}

        if instance.headers:
            parsed = email.parser.Parser().parsestr(instance.headers, True)
            for key in parsed.keys():
                headers[key] = parsed.get_all(key)
                # Let's return a single string instead of a list if only one
                # header with this key is present
                if len(headers[key]) == 1:
                    headers[key] = headers[key][0]

        return headers

    class Meta:
        model = Cover
        fields = CoverListSerializer.Meta.fields + (
            'headers', 'content')
        read_only_fields = fields
        extra_kwargs = CoverListSerializer.Meta.extra_kwargs
        versioned_fields = CoverListSerializer.Meta.versioned_fields


class CoverList(ListAPIView):
    """List cover letters."""

    serializer_class = CoverListSerializer
    filter_class = filterset_class = CoverFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'date', 'submitter')
    ordering = 'id'

    def get_queryset(self):
        return Cover.objects.all()\
            .prefetch_related('series__project')\
            .select_related('project', 'submitter', 'series')\
            .defer('content', 'headers')


class CoverDetail(RetrieveAPIView):
    """Show a cover letter."""

    serializer_class = CoverDetailSerializer

    def get_queryset(self):
        return Cover.objects.all()\
            .select_related('project', 'submitter', 'series')
