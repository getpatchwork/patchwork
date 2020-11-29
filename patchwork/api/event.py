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
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import EventFilterSet
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

    _category_map = {
        Event.CATEGORY_COVER_CREATED: ['cover'],
        Event.CATEGORY_PATCH_CREATED: ['patch'],
        Event.CATEGORY_PATCH_COMPLETED: ['patch', 'series'],
        Event.CATEGORY_PATCH_STATE_CHANGED: ['patch', 'previous_state',
                                             'current_state'],
        Event.CATEGORY_PATCH_DELEGATED: ['patch', 'previous_delegate',
                                         'current_delegate'],
        Event.CATEGORY_PATCH_RELATION_CHANGED: ['patch', 'previous_relation',
                                                'current_relation'],
        Event.CATEGORY_CHECK_CREATED: ['patch', 'created_check'],
        Event.CATEGORY_SERIES_CREATED: ['series'],
        Event.CATEGORY_SERIES_COMPLETED: ['series'],
    }

    def get_previous_relation(self, instance):
        return None

    def get_current_relation(self, instance):
        return None

    def to_representation(self, instance):
        data = super(EventSerializer, self).to_representation(instance)
        payload = OrderedDict()
        kept_fields = self._category_map[instance.category] + [
            'id', 'category', 'project', 'date', 'actor']

        for field in [x for x in data]:
            if field not in kept_fields:
                del data[field]
            elif field in self._category_map[instance.category]:
                field_name = 'check' if field == 'created_check' else field
                payload[field_name] = data.pop(field)

        data['payload'] = payload

        return data

    class Meta:
        model = Event
        fields = (
            'id', 'category', 'project', 'date', 'actor', 'patch',
            'series', 'cover', 'previous_state', 'current_state',
            'previous_delegate', 'current_delegate', 'created_check',
            'previous_relation', 'current_relation',
        )
        read_only_fields = fields
        versioned_fields = {
            '1.2': ('actor', ),
        }


class EventList(ListAPIView):
    """List events."""

    serializer_class = EventSerializer
    filter_class = filterset_class = EventFilterSet
    page_size_query_param = None  # fixed page size
    ordering_fields = ('date',)
    ordering = '-date'

    def get_queryset(self):
        return Event.objects.all()\
            .prefetch_related('project', 'patch__project', 'series__project',
                              'cover', 'previous_state', 'current_state',
                              'previous_delegate', 'current_delegate',
                              'created_check')
