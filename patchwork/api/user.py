# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.auth.models import User
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework import permissions
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import HyperlinkedModelSerializer

from patchwork.models import UserProfile
from patchwork.api.utils import has_version


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class UserProfileSerializer(ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ('send_email', 'items_per_page', 'show_ids')


class UserListSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'email')
        # we don't allow updating of emails via the API, as we need to
        # validate that the User actually owns said email first
        read_only_fields = ('username', 'email')
        extra_kwargs = {
            'url': {'view_name': 'api-user-detail'},
        }


class UserDetailSerializer(UserListSerializer):
    settings = UserProfileSerializer(source='profile')

    def update(self, instance, validated_data):
        settings_data = validated_data.pop('profile', None)

        request = self.context['request']
        if settings_data and has_version(request, '1.2') and (
                request.user.id == instance.id):
            # TODO(stephenfin): We ignore this field rather than raise an error
            # to be consistent with the rest of the API. We should change this
            # when we change the overall settings
            self.fields['settings'].update(instance.profile, settings_data)

        return super(UserDetailSerializer, self).update(
            instance, validated_data)

    def to_representation(self, instance):
        data = super(UserDetailSerializer, self).to_representation(instance)

        request = self.context['request']
        if not has_version(request, '1.2') or request.user.id != instance.id:
            del data['settings']

        return data

    class Meta:
        model = User
        fields = UserListSerializer.Meta.fields + ('settings',)
        # we don't allow updating of emails via the API, as we need to
        # validate that the User actually owns said email first
        read_only_fields = UserListSerializer.Meta.read_only_fields
        versioned_fields = {
            '1.2': ('settings',),
        }
        extra_kwargs = UserListSerializer.Meta.extra_kwargs


class UserMixin(object):

    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)


class UserList(UserMixin, ListAPIView):
    """List users."""

    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering_fields = ('id', 'username', 'email')
    ordering = 'id'
    serializer_class = UserListSerializer


class UserDetail(UserMixin, RetrieveUpdateAPIView):
    """
    get:
    Show a user.

    patch:
    Update a user.

    put:
    Update a user.
    """

    serializer_class = UserDetailSerializer
