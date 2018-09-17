# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from patchwork.api.embedded import UserSerializer
from patchwork.models import Person


class PersonSerializer(HyperlinkedModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = Person
        fields = ('id', 'url', 'name', 'email', 'user')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-person-detail'},
        }


class PersonMixin(object):

    permission_classes = (IsAuthenticated,)
    serializer_class = PersonSerializer

    def get_queryset(self):
        return Person.objects.all().prefetch_related('user')


class PersonList(PersonMixin, ListAPIView):
    """List users."""

    search_fields = ('name', 'email')
    ordering_fields = ('id', 'name', 'email')
    ordering = 'id'


class PersonDetail(PersonMixin, RetrieveAPIView):
    """Show a user."""

    pass
