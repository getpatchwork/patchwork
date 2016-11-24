# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

    pass


class UserDetail(UserMixin, RetrieveUpdateAPIView):
    """Show a user."""

    pass
