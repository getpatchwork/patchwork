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

import email.parser

from django.core.urlresolvers import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.serializers import ChoiceField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import PatchworkPermission
from patchwork.api.base import STATE_CHOICES
from patchwork.models import Patch
from patchwork.models import State


class StateField(ChoiceField):
    """Avoid the need for a state endpoint."""

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = STATE_CHOICES
        super(StateField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data = ' '.join(data.split('-'))
        try:
            return State.objects.get(name__iexact=data)
        except State.DoesNotExist:
            raise ValidationError('Invalid state. Expected one of: %s ' %
                                  ', '.join(STATE_CHOICES))

    def to_representation(self, obj):
        return '-'.join(obj.name.lower().split())


class PatchListSerializer(HyperlinkedModelSerializer):
    mbox = SerializerMethodField()
    state = StateField()
    tags = SerializerMethodField()
    check = SerializerMethodField()
    checks = SerializerMethodField()

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def get_tags(self, instance):
        if instance.project.tags:
            return {x.name: getattr(instance, x.attr_name)
                    for x in instance.project.tags}
        else:
            return None

    def get_check(self, instance):
        return instance.combined_check_state

    def get_checks(self, instance):
        return self.context.get('request').build_absolute_uri(
            reverse('api-check-list', kwargs={'patch_id': instance.id}))

    class Meta:
        model = Patch
        fields = ('id', 'url', 'project', 'msgid', 'date', 'name',
                  'commit_ref', 'pull_url', 'state', 'archived', 'hash',
                  'submitter', 'delegate', 'mbox', 'series', 'check', 'checks',
                  'tags')
        read_only_fields = ('project', 'msgid', 'date', 'name', 'hash',
                            'submitter', 'mbox', 'mbox', 'series', 'check',
                            'checks', 'tags')
        extra_kwargs = {
            'url': {'view_name': 'api-patch-detail'},
            'project': {'view_name': 'api-project-detail'},
            'submitter': {'view_name': 'api-person-detail'},
            'delegate': {'view_name': 'api-user-detail'},
            'series': {'view_name': 'api-series-detail',
                       'lookup_url_kwarg': 'pk'},
        }


class PatchDetailSerializer(PatchListSerializer):
    headers = SerializerMethodField()

    def get_headers(self, patch):
        if patch.headers:
            return email.parser.Parser().parsestr(patch.headers, True)

    class Meta:
        model = Patch
        fields = PatchListSerializer.Meta.fields + (
            'headers', 'content', 'diff')
        read_only_fields = PatchListSerializer.Meta.read_only_fields + (
            'headers', 'content', 'diff')
        extra_kwargs = PatchListSerializer.Meta.extra_kwargs


class PatchList(ListAPIView):
    """List patches."""

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchListSerializer

    def get_queryset(self):
        return Patch.objects.all().with_tag_counts()\
            .prefetch_related('series', 'check_set')\
            .select_related('state', 'submitter', 'delegate')\
            .defer('content', 'diff', 'headers')


class PatchDetail(RetrieveUpdateAPIView):
    """Show a patch."""

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchDetailSerializer

    def get_queryset(self):
        return Patch.objects.all().with_tag_counts()\
            .prefetch_related('series', 'check_set')\
            .select_related('state', 'submitter', 'delegate')
