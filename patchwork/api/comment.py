# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from django.http import Http404
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.serializers import HiddenField
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import MultipleFieldLookupMixin
from patchwork.api.base import PatchworkPermission
from patchwork.api.base import CurrentPatchDefault
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
        extra_kwargs = {
            'url': {'view_name': 'api-patch-comment-detail'},
        }


class CoverCommentListSerializer(BaseCommentListSerializer):

    class Meta:
        model = CoverComment
        fields = BaseCommentListSerializer.Meta.fields
        read_only_fields = fields
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields


class PatchCommentSerializer(BaseCommentListSerializer):

    patch = HiddenField(default=CurrentPatchDefault())

    class Meta:
        model = PatchComment
        fields = BaseCommentListSerializer.Meta.fields + (
            'patch', 'addressed')
        read_only_fields = fields[:-1]  # stay able to write to addressed field
        extra_kwargs = {
            'url': {'view_name': 'api-patch-comment-detail'}
        }
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields


class PatchCommentMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchCommentSerializer

    def get_queryset(self):
        patch_id = self.kwargs['patch_id']
        if not Patch.objects.filter(pk=self.kwargs['patch_id']).exists():
            raise Http404

        return PatchComment.objects.filter(
            patch=patch_id
        ).select_related('submitter')


class CoverCommentList(ListAPIView):
    """List cover comments"""

    permission_classes = (PatchworkPermission,)
    serializer_class = CoverCommentListSerializer
    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        if not Cover.objects.filter(pk=self.kwargs['pk']).exists():
            raise Http404

        return CoverComment.objects.filter(
            cover=self.kwargs['pk']
        ).select_related('submitter')


class PatchCommentList(PatchCommentMixin, ListAPIView):
    """List comments"""

    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'patch_id'


class PatchCommentDetail(PatchCommentMixin, MultipleFieldLookupMixin,
                         RetrieveUpdateDestroyAPIView):
    """
    get:
    Show a patch comment.

    patch:
    Update a patch comment.

    put:
    Update a patch comment.
    """
    lookup_url_kwargs = ('patch_id', 'comment_id')
    lookup_fields = ('patch_id', 'id')
