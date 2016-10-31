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

from rest_framework.serializers import ListSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import PatchworkPermission
from patchwork.api.base import PatchworkViewSet
from patchwork.api.base import URLSerializer
from patchwork.models import Patch


class PatchListSerializer(ListSerializer):
    """Semi hack to make the list of patches more efficient"""
    def to_representation(self, data):
        del self.child.fields['content']
        del self.child.fields['headers']
        del self.child.fields['diff']
        return super(PatchListSerializer, self).to_representation(data)


class PatchSerializer(URLSerializer):
    mbox_url = SerializerMethodField()
    state = SerializerMethodField()

    class Meta:
        model = Patch
        list_serializer_class = PatchListSerializer
        read_only_fields = ('project', 'name', 'date', 'submitter', 'diff',
                            'content', 'hash', 'msgid')
        # there's no need to expose an entire "tags" endpoint, so we custom
        # render this field
        exclude = ('tags',)

    def get_state(self, obj):
        return obj.state.name

    def get_mbox_url(self, patch):
        request = self.context.get('request', None)
        return request.build_absolute_uri(patch.get_mbox_url())

    def to_representation(self, instance):
        data = super(PatchSerializer, self).to_representation(instance)
        data['checks_url'] = data['url'] + 'checks/'
        data['check'] = instance.combined_check_state
        headers = data.get('headers')
        if headers is not None:
            data['headers'] = email.parser.Parser().parsestr(headers, True)
        data['tags'] = [{'name': x.tag.name, 'count': x.count}
                        for x in instance.patchtag_set.all()]
        return data


class PatchViewSet(PatchworkViewSet):
    permission_classes = (PatchworkPermission,)
    serializer_class = PatchSerializer

    def get_queryset(self):
        qs = super(PatchViewSet, self).get_queryset(
        ).prefetch_related(
            'check_set', 'patchtag_set'
        ).select_related('state', 'submitter', 'delegate')
        if 'pk' not in self.kwargs:
            # we are doing a listing, we don't need these fields
            qs = qs.defer('content', 'diff', 'headers')
        return qs
