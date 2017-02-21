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

from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import BundleFilter
from patchwork.models import Bundle


class BundleSerializer(HyperlinkedModelSerializer):

    mbox = SerializerMethodField()

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    class Meta:
        model = Bundle
        fields = ('id', 'url', 'project', 'name', 'owner', 'patches',
                  'public', 'mbox')
        read_only_fields = ('owner', 'patches', 'mbox')
        extra_kwargs = {
            'url': {'view_name': 'api-bundle-detail'},
            'project': {'view_name': 'api-project-detail'},
            'owner': {'view_name': 'api-user-detail'},
            'patches': {'view_name': 'api-patch-detail'},
        }


class BundleMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = BundleSerializer

    def get_queryset(self):
        if not self.request.user.is_anonymous():
            bundle_filter = Q(owner=self.request.user) | Q(public=True)
        else:
            bundle_filter = Q(public=True)

        return Bundle.objects\
            .filter(bundle_filter)\
            .prefetch_related('patches',)\
            .select_related('owner', 'project')


class BundleList(BundleMixin, ListAPIView):
    """List bundles."""

    filter_class = BundleFilter
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'owner')


class BundleDetail(BundleMixin, RetrieveAPIView):
    """Show a bundle."""

    pass
