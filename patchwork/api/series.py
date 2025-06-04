# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import HyperlinkedRelatedField
from rest_framework.serializers import ValidationError

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
    dependencies = HyperlinkedRelatedField(
        read_only=True, view_name='api-series-detail', many=True
    )
    dependents = HyperlinkedRelatedField(
        read_only=True, view_name='api-series-detail', many=True
    )
    supersedes = HyperlinkedRelatedField(
        view_name='api-series-detail',
        queryset=Series.objects.select_related('project').all(),
        required=False,
        many=True,
    )
    superseded = HyperlinkedRelatedField(
        read_only=True,
        view_name='api-series-detail',
        many=True,
    )

    def update(self, instance, validated_data, *args, **kwargs):
        allowed_fields = {'supersedes'}
        incoming_fields = set(validated_data.keys())

        if not incoming_fields.issubset(allowed_fields):
            invalid_fields = incoming_fields - allowed_fields
            raise ValidationError(
                {
                    'detail': 'Cannot update fields: '
                    f"{', '.join(invalid_fields)}. Only 'supersedes' can be "
                    'updated.'
                }
            )

        if 'supersedes' in validated_data:
            supersedes = validated_data.pop('supersedes', [])

            if instance in supersedes:
                raise ValidationError(
                    {'detail': 'A series cannot be linked to itself.'}
                )

            if any(
                series.project != instance.project for series in supersedes
            ):
                raise ValidationError(
                    {'detail': 'Series must belong to the same project.'}
                )

            try:
                instance.supersedes.set(supersedes)
            except Series.DoesNotExist:
                raise ValidationError(
                    {'detail': 'Unable to find one of the referenced series'}
                )

        return instance

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def to_representation(self, instance):
        if not instance.project.show_dependencies:
            for field in ('dependencies', 'dependents'):
                if field in self.fields:
                    del self.fields[field]

        if not instance.project.show_series_versions:
            for field in ('supersedes', 'superseded'):
                if field in self.fields:
                    del self.fields[field]

        data = super().to_representation(instance)

        return data

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
            'total',
            'received_total',
            'received_all',
            'mbox',
            'cover_letter',
            'patches',
            'dependencies',
            'dependents',
            'supersedes',
            'superseded',
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
            'dependencies',
            'dependents',
            'superseded',
        )
        versioned_fields = {
            '1.1': ('web_url',),
            '1.4': ('dependencies', 'dependents', 'supersedes', 'superseded'),
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
                'dependencies',
                'dependents',
                'supersedes',
                'superseded',
            )
            .select_related('submitter', 'project')
        )


class SeriesList(SeriesMixin, ListAPIView):
    """List series."""

    filter_class = filterset_class = SeriesFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'date', 'submitter', 'received_all')
    ordering = 'id'


class SeriesDetail(SeriesMixin, RetrieveUpdateAPIView):
    """Show a series.

    retrieve:
        Return the details of a series.

    update:
        Only updates the 'supersedes' field of a series. Replaces the whole set
        of superseded series.

        ::

        Instance:
            instance.supersedes = [
                'http://example.com/api/series/1/',
                'http://example.com/api/series/2/',
                'http://example.com/api/series/5/'
            ]

        Request:
            PUT/PATCH {
                "supersedes": [
                    'http://example.com/api/series/1/',
                    'http://example.com/api/series/8/'
                ]
            }

        Result:
            instance.supersedes = [
                'http://example.com/api/series/1/',
                'http://example.com/api/series/8/'
            ]
    """

    # PUT operation will behave as a partial update
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
