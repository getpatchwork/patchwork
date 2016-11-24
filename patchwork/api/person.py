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

from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from patchwork.models import Person


class PersonSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = ('id', 'url', 'name', 'email', 'user')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-person-detail'},
            'user': {'view_name': 'api-user-detail'},
        }


class PersonMixin(object):

    queryset = Person.objects.prefetch_related('user')
    permission_classes = (IsAuthenticated,)
    serializer_class = PersonSerializer


class PersonList(PersonMixin, ListAPIView):
    """List users."""

    pass


class PersonDetail(PersonMixin, RetrieveAPIView):
    """Show a user."""

    pass
