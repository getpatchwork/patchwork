# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

import email.parser

import django
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import HyperlinkedRelatedField
from rest_framework.serializers import SerializerMethodField

from patchwork.api.filters import CoverLetterFilter
from patchwork.models import CoverLetter


class CoverLetterListSerializer(HyperlinkedModelSerializer):
    series = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='api-series-detail')

    class Meta:
        model = CoverLetter
        fields = ('id', 'url', 'project', 'msgid', 'date', 'name', 'submitter',
                  'series')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-cover-detail'},
            'project': {'view_name': 'api-project-detail'},
            'submitter': {'view_name': 'api-person-detail'},
        }


class CoverLetterDetailSerializer(CoverLetterListSerializer):
    headers = SerializerMethodField()

    def get_headers(self, instance):
        if instance.headers:
            return email.parser.Parser().parsestr(instance.headers, True)

    class Meta:
        model = CoverLetter
        fields = CoverLetterListSerializer.Meta.fields + ('headers', 'content')
        read_only_fields = CoverLetterListSerializer.Meta.read_only_fields + (
            'headers', 'content')
        extra_kwargs = CoverLetterListSerializer.Meta.extra_kwargs


class CoverLetterList(ListAPIView):
    """List cover letters."""

    serializer_class = CoverLetterListSerializer
    filter_class = CoverLetterFilter
    search_fields = ('name',)

    def get_queryset(self):
        qs = CoverLetter.objects.all().prefetch_related('series')\
            .select_related('submitter')

        # FIXME(stephenfin): This causes issues with Django 1.6 for whatever
        # reason. Suffer the performance hit on those versions.
        if django.VERSION >= (1, 7):
            qs.defer('content', 'headers')

        return qs


class CoverLetterDetail(RetrieveAPIView):
    """Show a cover letter."""

    serializer_class = CoverLetterDetailSerializer

    def get_queryset(self):
        return CoverLetter.objects.all().prefetch_related('series')\
            .select_related('submitter')
