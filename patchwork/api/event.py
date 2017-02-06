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

from django.core.urlresolvers import reverse
from rest_framework.generics import ListAPIView
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.filters import EventFilter
from patchwork.api.patch import StateField
from patchwork.models import Event


class EventSerializer(HyperlinkedModelSerializer):

    previous_state = StateField()
    current_state = StateField()
    created_check = SerializerMethodField()

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

    def get_created_check(self, instance):
        if not instance.patch or not instance.created_check:
            return

        return self.context.get('request').build_absolute_uri(
            reverse('api-check-detail', kwargs={
                'patch_id': instance.patch.id,
                'check_id': instance.created_check.id}))

    def to_representation(self, instance):
        data = super(EventSerializer, self).to_representation(instance)

        kept_fields = self._category_map[instance.category] + [
            'id', 'category', 'project', 'date']
        for field in [x for x in data if x not in kept_fields]:
            del data[field]

        return data

    class Meta:
        model = Event
        fields = ('id', 'category', 'project', 'date', 'patch', 'series',
                  'cover', 'previous_state', 'current_state',
                  'previous_delegate', 'current_delegate', 'created_check')
        read_only_fields = fields
        extra_kwargs = {
            'project': {'view_name': 'api-project-detail'},
            'patch': {'view_name': 'api-patch-detail'},
            'series': {'view_name': 'api-series-detail'},
            'cover': {'view_name': 'api-cover-detail'},
            'previous_delegate': {'view_name': 'api-user-detail'},
            'current_delegate': {'view_name': 'api-user-detail'},
            'created_check': {'view_name': 'api-check-detail'},
        }


class EventList(ListAPIView):
    """List events."""

    serializer_class = EventSerializer
    filter_class = EventFilter
    page_size_query_param = None  # fixed page size
    ordering = '-date'
    ordering_fields = ()

    def get_queryset(self):
        return Event.objects.all()\
            .select_related('project', 'patch', 'series', 'cover',
                            'previous_state', 'current_state',
                            'previous_delegate', 'current_delegate',
                            'created_check')\
            .order_by('-date')
