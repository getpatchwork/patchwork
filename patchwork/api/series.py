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

from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import SeriesFilter
from patchwork.models import Series


class SeriesSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = Series
        fields = ('id', 'url', 'project', 'name', 'date', 'submitter',
                  'version', 'total', 'received_total', 'received_all',
                  'cover_letter', 'patches')
        read_only_fields = ('date', 'submitter', 'total', 'received_total',
                            'received_all', 'cover_letter', 'patches')
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
            'project': {'view_name': 'api-project-detail'},
            'submitter': {'view_name': 'api-person-detail'},
            'cover_letter': {'view_name': 'api-cover-detail'},
            'patches': {'view_name': 'api-patch-detail'},
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


class SeriesDetail(SeriesMixin, RetrieveAPIView):
    """Show a series."""

    pass
