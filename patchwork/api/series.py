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

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import SeriesFilter
from patchwork.api.embedded import CoverLetterSerializer
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.models import Series


class SeriesSerializer(HyperlinkedModelSerializer):

    project = ProjectSerializer(read_only=True)
    submitter = PersonSerializer(read_only=True)
    mbox = SerializerMethodField()
    cover_letter = CoverLetterSerializer(read_only=True)
    patches = PatchSerializer(read_only=True, many=True)

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    class Meta:
        model = Series
        fields = ('id', 'url', 'project', 'name', 'date', 'submitter',
                  'version', 'total', 'received_total', 'received_all',
                  'mbox', 'cover_letter', 'patches')
        read_only_fields = ('date', 'submitter', 'total', 'received_total',
                            'received_all', 'mbox', 'cover_letter', 'patches')
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
        }


class SeriesMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = SeriesSerializer

    def get_queryset(self):
        return Series.objects.all().prefetch_related('patches',)\
            .select_related('submitter', 'cover_letter', 'project')


class SeriesList(SeriesMixin, ListAPIView):
    """List series."""

    filter_class = SeriesFilter
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'date', 'submitter', 'received_all')
    ordering = 'id'


class SeriesDetail(SeriesMixin, RetrieveAPIView):
    """Show a series."""

    pass
