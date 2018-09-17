# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.auth.models import User
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework import permissions
from rest_framework.serializers import HyperlinkedModelSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class UserSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'email')
        # we don't allow updating of emails via the API, as we need to
        # validate that the User actually owns said email first
        read_only_fields = ('username', 'email')
        extra_kwargs = {
            'url': {'view_name': 'api-user-detail'},
        }


class UserMixin(object):

    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = UserSerializer


class UserList(UserMixin, ListAPIView):
    """List users."""

    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering_fields = ('id', 'username', 'email')
    ordering = 'id'


class UserDetail(UserMixin, RetrieveUpdateAPIView):
    """Show a user."""

    pass
