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

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import CurrentUserDefault
from rest_framework.serializers import HiddenField
from rest_framework.serializers import HyperlinkedModelSerializer

from patchwork.api.base import CheckHyperlinkedIdentityField
from patchwork.api.base import MultipleFieldLookupMixin
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import CheckFilter
from patchwork.models import Check
from patchwork.models import Patch


class CurrentPatchDefault(object):
    def set_context(self, serializer_field):
        self.patch = serializer_field.context['request'].patch

    def __call__(self):
        return self.patch


class CheckSerializer(HyperlinkedModelSerializer):

    url = CheckHyperlinkedIdentityField('api-check-detail')
    patch = HiddenField(default=CurrentPatchDefault())
    user = UserSerializer(read_only=True, default=CurrentUserDefault())

    def run_validation(self, data):
        for val, label in Check.STATE_CHOICES:
            if label == data['state']:
                data['state'] = val
                break
        return super(CheckSerializer, self).run_validation(data)

    def to_representation(self, instance):
        data = super(CheckSerializer, self).to_representation(instance)
        data['state'] = instance.get_state_display()
        return data

    class Meta:
        model = Check
        fields = ('id', 'url', 'patch', 'user', 'date', 'state', 'target_url',
                  'context', 'description')
        read_only_fields = ('date',)
        extra_kwargs = {
            'url': {'view_name': 'api-check-detail'},
        }


class CheckMixin(object):

    serializer_class = CheckSerializer
    filter_class = CheckFilter

    def get_queryset(self):
        return Check.objects.prefetch_related('patch', 'user')


class CheckListCreate(CheckMixin, ListCreateAPIView):
    """List or create checks."""

    lookup_url_kwarg = 'patch_id'
    ordering = 'id'

    def create(self, request, patch_id, *args, **kwargs):
        p = Patch.objects.get(id=patch_id)
        if not p.is_editable(request.user):
            raise PermissionDenied()
        request.patch = p
        return super(CheckListCreate, self).create(request, *args, **kwargs)


class CheckDetail(CheckMixin, MultipleFieldLookupMixin, RetrieveAPIView):
    """Show a check."""

    lookup_url_kwargs = ('patch_id', 'check_id')
    lookup_fields = ('patch_id', 'id')
