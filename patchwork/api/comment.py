# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from rest_framework.generics import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.embedded import PersonSerializer
from patchwork.models import Cover
from patchwork.models import CoverComment
from patchwork.models import Patch
from patchwork.models import PatchComment


class BaseCommentListSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    subject = SerializerMethodField()
    headers = SerializerMethodField()
    submitter = PersonSerializer(read_only=True)

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_subject(self, comment):
        return email.parser.Parser().parsestr(comment.headers,
                                              True).get('Subject', '')

    def get_headers(self, comment):
        headers = {}

        if comment.headers:
            parsed = email.parser.Parser().parsestr(comment.headers, True)
            for key in parsed.keys():
                headers[key] = parsed.get_all(key)
                # Let's return a single string instead of a list if only one
                # header with this key is present
                if len(headers[key]) == 1:
                    headers[key] = headers[key][0]

        return headers

    class Meta:
        fields = ('id', 'web_url', 'msgid', 'list_archive_url', 'date',
                  'subject', 'submitter', 'content', 'headers')
        read_only_fields = fields
        versioned_fields = {
            '1.1': ('web_url', ),
            '1.2': ('list_archive_url',),
        }


class CoverCommentListSerializer(BaseCommentListSerializer):

    class Meta:
        model = CoverComment
        fields = BaseCommentListSerializer.Meta.fields
        read_only_fields = fields
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields


class PatchCommentListSerializer(BaseCommentListSerializer):

    class Meta:
        model = PatchComment
        fields = BaseCommentListSerializer.Meta.fields
        read_only_fields = fields
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields


class CoverCommentList(ListAPIView):
    """List cover comments"""

    permission_classes = (PatchworkPermission,)
    serializer_class = CoverCommentListSerializer
    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        get_object_or_404(Cover, pk=self.kwargs['pk'])

        return CoverComment.objects.filter(
            cover=self.kwargs['pk']
        ).select_related('submitter')


class PatchCommentList(ListAPIView):
    """List comments"""

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchCommentListSerializer
    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'patch_id'

    def get_queryset(self):
        get_object_or_404(Patch, id=self.kwargs['patch_id'])

        return PatchComment.objects.filter(
            patch=self.kwargs['patch_id']
        ).select_related('submitter')
