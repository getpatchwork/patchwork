# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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

from collections import OrderedDict

from rest_framework.generics import ListAPIView
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.embedded import CheckSerializer
from patchwork.api.embedded import CoverLetterSerializer
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import EventFilter
from patchwork.api.patch import StateField
from patchwork.models import Event


class EventSerializer(ModelSerializer):

    project = ProjectSerializer(read_only=True)
    patch = PatchSerializer(read_only=True)
    series = SeriesSerializer(read_only=True)
    cover = CoverLetterSerializer(read_only=True)
    previous_state = StateField()
    current_state = StateField()
    previous_delegate = UserSerializer()
    current_delegate = UserSerializer()
    created_check = SerializerMethodField()
    created_check = CheckSerializer()

    _category_map = {
        Event.CATEGORY_COVER_CREATED: ['cover'],
        Event.CATEGORY_PATCH_CREATED: ['patch'],
        Event.CATEGORY_PATCH_COMPLETED: ['patch', 'series'],
        Event.CATEGORY_PATCH_STATE_CHANGED: ['patch', 'previous_state',
                                             'current_state'],
        Event.CATEGORY_PATCH_DELEGATED: ['patch', 'previous_delegate',
                                         'current_delegate'],
        Event.CATEGORY_CHECK_CREATED: ['patch', 'created_check'],
        Event.CATEGORY_SERIES_CREATED: ['series'],
        Event.CATEGORY_SERIES_COMPLETED: ['series'],
    }

    def to_representation(self, instance):
        data = super(EventSerializer, self).to_representation(instance)
        payload = OrderedDict()
        kept_fields = self._category_map[instance.category] + [
            'id', 'category', 'project', 'date']

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
        fields = ('id', 'category', 'project', 'date', 'patch', 'series',
                  'cover', 'previous_state', 'current_state',
                  'previous_delegate', 'current_delegate', 'created_check')
        read_only_fields = fields


class EventList(ListAPIView):
    """List events."""

    serializer_class = EventSerializer
    filter_class = EventFilter
    page_size_query_param = None  # fixed page size
    ordering_fields = ()
    ordering = '-date'

    def get_queryset(self):
        return Event.objects.all()\
            .prefetch_related('project', 'patch', 'series', 'cover',
                              'previous_state', 'current_state',
                              'previous_delegate', 'current_delegate',
                              'created_check')
