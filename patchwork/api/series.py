# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import SeriesFilterSet
from patchwork.api.embedded import CoverSerializer
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.models import Series


class SeriesSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    submitter = PersonSerializer(read_only=True)
    mbox = SerializerMethodField()
    cover_letter = CoverSerializer(read_only=True)
    patches = PatchSerializer(read_only=True, many=True)

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    class Meta:
        model = Series
        fields = ('id', 'url', 'web_url', 'project', 'name', 'date',
                  'submitter', 'version', 'total', 'received_total',
                  'received_all', 'mbox', 'cover_letter', 'patches')
        read_only_fields = ('date', 'submitter', 'total', 'received_total',
                            'received_all', 'mbox', 'cover_letter', 'patches')
        versioned_fields = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
        }


class SeriesMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = SeriesSerializer

    def get_queryset(self):
        return Series.objects.all()\
            .prefetch_related('patches__project', 'cover_letter__project')\
            .select_related('submitter', 'project')


class SeriesList(SeriesMixin, ListAPIView):
    """List series."""

    filter_class = filterset_class = SeriesFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'date', 'submitter', 'received_all')
    ordering = 'id'


class SeriesDetail(SeriesMixin, RetrieveAPIView):
    """Show a series."""

    pass
