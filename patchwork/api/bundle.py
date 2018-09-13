# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import BundleFilterSet
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.models import Bundle


class BundleSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    mbox = SerializerMethodField()
    owner = UserSerializer(read_only=True)
    patches = PatchSerializer(many=True, read_only=True)

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    class Meta:
        model = Bundle
        fields = ('id', 'url', 'web_url', 'project', 'name', 'owner',
                  'patches', 'public', 'mbox')
        read_only_fields = ('owner', 'patches', 'mbox')
        versioned_fields = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-bundle-detail'},
        }


class BundleMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = BundleSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            bundle_filter = Q(owner=self.request.user) | Q(public=True)
        else:
            bundle_filter = Q(public=True)

        return Bundle.objects\
            .filter(bundle_filter)\
            .prefetch_related('patches',)\
            .select_related('owner', 'project')


class BundleList(BundleMixin, ListAPIView):
    """List bundles."""

    filter_class = filterset_class = BundleFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'owner')
    ordering = 'id'


class BundleDetail(BundleMixin, RetrieveAPIView):
    """Show a bundle."""

    pass
