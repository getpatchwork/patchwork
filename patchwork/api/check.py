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

from django.core.urlresolvers import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.response import Response
from rest_framework.serializers import CurrentUserDefault
from rest_framework.serializers import HiddenField
from rest_framework.serializers import ModelSerializer

from patchwork.api.base import PatchworkViewSet
from patchwork.models import Check
from patchwork.models import Patch


class CurrentPatchDefault(object):
    def set_context(self, serializer_field):
        self.patch = serializer_field.context['request'].patch

    def __call__(self):
        return self.patch


class CheckSerializer(ModelSerializer):
    user = HyperlinkedRelatedField(
        'user-detail', read_only=True, default=CurrentUserDefault())
    patch = HiddenField(default=CurrentPatchDefault())

    def run_validation(self, data):
        for val, label in Check.STATE_CHOICES:
            if label == data['state']:
                data['state'] = val
                break
        return super(CheckSerializer, self).run_validation(data)

    def to_representation(self, instance):
        data = super(CheckSerializer, self).to_representation(instance)
        data['state'] = instance.get_state_display()
        # drf-nested doesn't handle HyperlinkedModelSerializers properly,
        # so we have to put the url in by hand here.
        url = self.context['request'].build_absolute_uri(reverse(
            'api_1.0:patch-detail', args=[instance.patch.id]))
        data['url'] = url + 'checks/%s/' % instance.id
        return data

    class Meta:
        model = Check
        fields = ('patch', 'user', 'date', 'state', 'target_url',
                  'context', 'description')
        read_only_fields = ('date',)


class CheckViewSet(PatchworkViewSet):
    serializer_class = CheckSerializer

    def not_allowed(self, request, **kwargs):
        raise PermissionDenied()

    update = not_allowed
    partial_update = not_allowed
    destroy = not_allowed

    def create(self, request, patch_pk):
        p = Patch.objects.get(id=patch_pk)
        if not p.is_editable(request.user):
            raise PermissionDenied()
        request.patch = p
        return super(CheckViewSet, self).create(request)

    def list(self, request, patch_pk):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(patch=patch_pk)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
