# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.db.models import Q
from rest_framework import exceptions
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework import permissions
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import ValidationError

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import BundleFilterSet
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.api import utils
from patchwork.models import Bundle


class BundlePermission(permissions.BasePermission):
    """Ensure the API version, if configured, is >= v1.2.

    Bundle creation/updating was only added in API v1.2 and we don't want to
    change behavior in older API versions.
    """
    def has_permission(self, request, view):
        # read-only permission for everything
        if request.method in permissions.SAFE_METHODS:
            return True

        if not utils.has_version(request, '1.2'):
            raise exceptions.MethodNotAllowed(request.method)

        if request.method == 'POST' and (
                not request.user or not request.user.is_authenticated):
            return False

        # we have more to do but we can't do that until we have an object
        return True

    def has_object_permission(self, request, view, obj):
        if (request.user and
                request.user.is_authenticated and
                request.user == obj.owner):
            return True

        if not obj.public:
            # if the bundle isn't public, we don't want to leak the fact that
            # it exists
            raise exceptions.NotFound

        return request.method in permissions.SAFE_METHODS


class BundleSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    mbox = SerializerMethodField()
    owner = UserSerializer(read_only=True)
    patches = PatchSerializer(many=True, required=True,
                              style={'base_template': 'input.html'})

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def create(self, validated_data):
        patches = validated_data.pop('patches')
        instance = super(BundleSerializer, self).create(validated_data)
        instance.overwrite_patches(patches)
        return instance

    def update(self, instance, validated_data):
        patches = validated_data.pop('patches', None)
        instance = super(BundleSerializer, self).update(
            instance, validated_data)
        if patches:
            instance.overwrite_patches(patches)
        return instance

    def validate_patches(self, value):
        if not len(value):
            raise ValidationError('Bundles cannot be empty')

        if len(set([p.project.id for p in value])) > 1:
            raise ValidationError('Bundle patches must belong to the same '
                                  'project')

        return value

    def validate(self, data):
        if data.get('patches'):
            data['project'] = data['patches'][0].project

        return super(BundleSerializer, self).validate(data)

    class Meta:
        model = Bundle
        fields = ('id', 'url', 'web_url', 'project', 'name', 'owner',
                  'patches', 'public', 'mbox')
        read_only_fields = ('project', 'owner', 'mbox')
        versioned_fields = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-bundle-detail'},
        }


class BundleMixin(object):

    permission_classes = [PatchworkPermission & BundlePermission]
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


class BundleList(BundleMixin, ListCreateAPIView):
    """List or create bundles."""

    filter_class = filterset_class = BundleFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'owner')
    ordering = 'id'

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BundleDetail(BundleMixin, RetrieveUpdateDestroyAPIView):
    """
    get:
    Show a bundle.

    patch:
    Update a bundle.

    put:
    Update a bundle.

    delete:
    Delete a bundle.
    """
