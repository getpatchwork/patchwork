# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.serializers import SerializerMethodField
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import SeriesFilterSet
from patchwork.api.embedded import CoverSerializer
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer as RelatedSeriesSerializer
from patchwork.models import Series


class SeriesSerializer(BaseHyperlinkedModelSerializer):
    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    submitter = PersonSerializer(read_only=True)
    mbox = SerializerMethodField()
    cover_letter = CoverSerializer(read_only=True)
    patches = PatchSerializer(read_only=True, many=True)
    previous_series = RelatedSeriesSerializer(many=True, default=[])
    subsequent_series = RelatedSeriesSerializer(many=True, default=[])
    required_series = RelatedSeriesSerializer(many=True, default=[])
    required_by_series = RelatedSeriesSerializer(many=True, default=[])

    def helper_get_series_urls(self, series_queryset):
        return [self.get_web_url(series) for series in series_queryset]

    def helper_validate_series(self, related_series):
        for series in related_series:
            if self.instance.id == series.id:
                raise ValidationError('A series cannot be linked to itself.')
            if self.instance.project.id != series.project.id:
                raise ValidationError(
                    'Series must belong to the same project.'
                )
        return related_series

    def get_previous_series(self, obj):
        previous = obj.previous_series.all()
        return self.helper_get_series_urls(previous)

    def get_subsequent_series(self, obj):
        subsequent = obj.subsequent_series.all()
        return self.helper_get_series_urls(subsequent)

    def get_required_series(self, obj):
        required = obj.required_series.all()
        return self.helper_get_series_urls(required)

    def get_required_by_series(self, obj):
        required_by = obj.required_by_series.all()
        return self.helper_get_series_urls(required_by)

    def validate_previous_series(self, previous_series):
        return self.helper_validate_series(previous_series)

    def validate_subsequent_series(self, subsequent_series):
        return self.helper_validate_series(subsequent_series)

    def validate_required_series(self, required_series):
        return self.helper_validate_series(required_series)

    def validate_required_by_series(self, required_by_series):
        return self.helper_validate_series(required_by_series)

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    class Meta:
        model = Series
        fields = (
            'id',
            'url',
            'web_url',
            'project',
            'name',
            'date',
            'submitter',
            'version',
            'previous_series',
            'subsequent_series',
            'required_series',
            'required_by_series',
            'total',
            'received_total',
            'received_all',
            'mbox',
            'cover_letter',
            'patches',
        )
        read_only_fields = (
            'date',
            'submitter',
            'total',
            'received_total',
            'received_all',
            'mbox',
            'cover_letter',
            'patches',
        )
        versioned_fields = {
            '1.1': ('web_url',),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
        }


class SeriesMixin(object):
    permission_classes = (PatchworkPermission,)
    serializer_class = SeriesSerializer

    def get_queryset(self):
        return (
            Series.objects.all()
            .prefetch_related(
                'patches__project',
                'cover_letter__project',
                'previous_series__project',
                'subsequent_series__project',
                'required_series__project',
                'required_by_series__project',
            )
            .select_related('submitter', 'project')
        )


class SeriesList(SeriesMixin, ListAPIView):
    """List series."""

    filter_class = filterset_class = SeriesFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'date', 'submitter', 'received_all')
    ordering = 'id'


class SeriesDetail(SeriesMixin, RetrieveAPIView, UpdateAPIView):
    """Show and update a series."""

    queryset = Series.objects.all()
    serializer_class = SeriesSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        allowed_fields = {
            'previous_series',
            'subsequent_series',
            'required_series',
            'required_by_series',
        }
        provided_fields = set(request.data.keys())
        disallowed_fields = provided_fields - allowed_fields

        if disallowed_fields:
            raise ValidationError(
                {
                    'error': 'Invalid fields in request.',
                    'invalid_fields': list(disallowed_fields),
                }
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
