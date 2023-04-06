# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from collections import OrderedDict

from rest_framework.generics import ListAPIView
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import SlugRelatedField

from patchwork.api.embedded import CheckSerializer
from patchwork.api.embedded import CoverSerializer
from patchwork.api.embedded import CoverCommentSerializer
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import PatchCommentSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import EventFilterSet
from patchwork.api import utils
from patchwork.models import Event


class EventSerializer(ModelSerializer):
    project = ProjectSerializer(read_only=True)
    actor = UserSerializer()
    patch = PatchSerializer(read_only=True)
    series = SeriesSerializer(read_only=True)
    cover = CoverSerializer(read_only=True)
    previous_state = SlugRelatedField(slug_field='slug', read_only=True)
    current_state = SlugRelatedField(slug_field='slug', read_only=True)
    previous_delegate = UserSerializer()
    current_delegate = UserSerializer()
    created_check = SerializerMethodField()
    created_check = CheckSerializer()
    previous_relation = SerializerMethodField()
    current_relation = SerializerMethodField()
    cover_comment = CoverCommentSerializer()
    patch_comment = PatchCommentSerializer()

    # Mapping of event type to fields to include in the response
    _category_map = {
        Event.CATEGORY_COVER_CREATED: ['cover'],
        Event.CATEGORY_PATCH_CREATED: ['patch'],
        Event.CATEGORY_PATCH_COMPLETED: ['patch', 'series'],
        Event.CATEGORY_PATCH_STATE_CHANGED: [
            'patch',
            'previous_state',
            'current_state',
        ],
        Event.CATEGORY_PATCH_DELEGATED: [
            'patch',
            'previous_delegate',
            'current_delegate',
        ],
        Event.CATEGORY_PATCH_RELATION_CHANGED: [
            'patch',
            'previous_relation',
            'current_relation',
        ],
        Event.CATEGORY_CHECK_CREATED: ['patch', 'created_check'],
        Event.CATEGORY_SERIES_CREATED: ['series'],
        Event.CATEGORY_SERIES_COMPLETED: ['series'],
        Event.CATEGORY_COVER_COMMENT_CREATED: ['cover', 'cover_comment'],
        Event.CATEGORY_PATCH_COMMENT_CREATED: ['patch', 'patch_comment'],
    }

    # Mapping of database column names to REST API representations
    _field_name_map = {
        'created_check': 'check',
        'cover_comment': 'comment',
        'patch_comment': 'comment',
    }

    def get_previous_relation(self, instance):
        return None

    def get_current_relation(self, instance):
        return None

    def to_representation(self, instance):
        data = super(EventSerializer, self).to_representation(instance)
        payload = OrderedDict()
        kept_fields = self._category_map[instance.category] + [
            'id',
            'category',
            'project',
            'date',
            'actor',
        ]

        for field in [x for x in data]:
            if field not in kept_fields:
                del data[field]
            elif field in self._category_map[instance.category]:
                # remap fields if necessary
                field_name = self._field_name_map.get(field, field)
                payload[field_name] = data.pop(field)

        data['payload'] = payload

        return data

    class Meta:
        model = Event
        fields = (
            'id',
            'category',
            'project',
            'date',
            'actor',
            'patch',
            'series',
            'cover',
            'previous_state',
            'current_state',
            'previous_delegate',
            'current_delegate',
            'created_check',
            'previous_relation',
            'current_relation',
            'cover_comment',
            'patch_comment',
        )
        read_only_fields = fields
        versioned_fields = {
            '1.2': ('actor',),
        }


class EventList(ListAPIView):
    """List events."""

    serializer_class = EventSerializer
    filter_class = filterset_class = EventFilterSet
    page_size_query_param = None  # fixed page size
    ordering_fields = ('date',)
    ordering = '-date'

    def get_queryset(self):
        events = Event.objects.all().prefetch_related(
            'project',
            'patch__project',
            'series__project',
            'cover',
            'previous_state',
            'current_state',
            'previous_delegate',
            'current_delegate',
            'created_check',
        )
        # NOTE(stephenfin): We need to exclude comment-related events because
        # until API v1.3, we didn't have an comment detail API to point to.
        # This goes against our pledge to version events in the docs but must
        # be done.
        # TODO(stephenfin): Make this more generic.
        if utils.has_version(self.request, '1.3'):
            events = events.prefetch_related(
                'cover_comment',
                'cover_comment__cover__project',
                'patch_comment',
                'patch_comment__patch__project',
            )
        else:
            events = events.exclude(
                category__in=[
                    Event.CATEGORY_COVER_COMMENT_CREATED,
                    Event.CATEGORY_PATCH_COMMENT_CREATED,
                ]
            )
        return events
