# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.http.request import QueryDict

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import CurrentUserDefault
from rest_framework.serializers import HiddenField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import ValidationError

from patchwork.api.base import CheckHyperlinkedIdentityField
from patchwork.api.base import MultipleFieldLookupMixin
from patchwork.api.base import CurrentPatchDefault
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import CheckFilterSet
from patchwork.models import Check
from patchwork.models import Patch


class CheckSerializer(HyperlinkedModelSerializer):

    url = CheckHyperlinkedIdentityField('api-check-detail')
    patch = HiddenField(default=CurrentPatchDefault())
    user = UserSerializer(default=CurrentUserDefault())

    def run_validation(self, data):
        if 'state' not in data or data['state'] == '':
            raise ValidationError({'state': ["A check must have a state."]})

        for val, label in Check.STATE_CHOICES:
            if label != data['state']:
                continue

            if isinstance(data, QueryDict):  # form-data request
                # NOTE(stephenfin): 'data' is essentially 'request.POST', which
                # is immutable by default. However, there's no good reason for
                # this to be this way [1], so temporarily unset that mutability
                # to fix what we need to here.
                #
                # [1] http://stackoverflow.com/a/12619745/613428
                mutable = data._mutable  # noqa
                data._mutable = True  # noqa
                data['state'] = val
                data._mutable = mutable  # noqa
            else:  # json request
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
    filter_class = filterset_class = CheckFilterSet

    def get_queryset(self):
        patch_id = self.kwargs['patch_id']

        # ensure the patch exists
        get_object_or_404(Patch, id=self.kwargs['patch_id'])

        return Check.objects.prefetch_related('user').filter(patch=patch_id)


class CheckListCreate(CheckMixin, ListCreateAPIView):
    """
    get:
    List checks.

    post:
    Create a check.
    """

    lookup_url_kwarg = 'patch_id'
    ordering = 'id'

    def create(self, request, patch_id, *args, **kwargs):
        p = get_object_or_404(Patch, id=patch_id)
        if not p.is_editable(request.user):
            raise PermissionDenied()
        request.patch = p
        return super(CheckListCreate, self).create(request, *args, **kwargs)


class CheckDetail(CheckMixin, MultipleFieldLookupMixin, RetrieveAPIView):
    """Show a check."""

    lookup_url_kwargs = ('patch_id', 'check_id')
    lookup_fields = ('patch_id', 'id')
