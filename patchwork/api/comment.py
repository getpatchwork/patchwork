# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from rest_framework.generics import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.serializers import HiddenField
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import MultipleFieldLookupMixin
from patchwork.api.base import PatchworkPermission
from patchwork.api.base import CurrentCoverDefault
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
                  'subject', 'submitter', 'content', 'headers', 'addressed')
        read_only_fields = ('id', 'web_url', 'msgid', 'list_archive_url',
                            'date', 'subject', 'submitter', 'content',
                            'headers')
        versioned_fields = {
            '1.1': ('web_url', ),
            '1.2': ('list_archive_url',),
            '1.3': ('addressed',),
        }


class CoverCommentSerializer(BaseCommentListSerializer):

    cover = HiddenField(default=CurrentCoverDefault())

    class Meta:
        model = CoverComment
        fields = BaseCommentListSerializer.Meta.fields + (
            'cover', 'addressed')
        read_only_fields = BaseCommentListSerializer.Meta.read_only_fields + (
            'cover', )
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields
        extra_kwargs = {
            'url': {'view_name': 'api-cover-comment-detail'}
        }


class CoverCommentMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = CoverCommentSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        comment_id = self.kwargs['comment_id']
        obj = get_object_or_404(queryset, id=comment_id)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        cover_id = self.kwargs['cover_id']
        get_object_or_404(Cover, pk=cover_id)

        return CoverComment.objects.filter(
            cover=cover_id
        ).select_related('submitter')


class PatchCommentSerializer(BaseCommentListSerializer):

    patch = HiddenField(default=CurrentPatchDefault())

    class Meta:
        model = PatchComment
        fields = BaseCommentListSerializer.Meta.fields + ('patch', )
        read_only_fields = BaseCommentListSerializer.Meta.read_only_fields + (
            'patch', )
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields
        extra_kwargs = {
            'url': {'view_name': 'api-patch-comment-detail'}
        }


class PatchCommentMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchCommentSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        comment_id = self.kwargs['comment_id']
        obj = get_object_or_404(queryset, id=comment_id)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        patch_id = self.kwargs['patch_id']
        get_object_or_404(Patch, id=patch_id)

        return PatchComment.objects.filter(
            patch=patch_id
        ).select_related('submitter')


class CoverCommentList(CoverCommentMixin, ListAPIView):
    """List cover comments"""

    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'cover_id'


class CoverCommentDetail(CoverCommentMixin, MultipleFieldLookupMixin,
                         RetrieveUpdateAPIView):
    """
    get:
    Show a cover comment.

    patch:
    Update a cover comment.

    put:
    Update a cover comment.
    """
    lookup_url_kwargs = ('cover_id', 'comment_id')
    lookup_fields = ('cover_id', 'id')


class PatchCommentList(PatchCommentMixin, ListAPIView):
    """List patch comments"""

    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'patch_id'


class PatchCommentDetail(PatchCommentMixin, MultipleFieldLookupMixin,
                         RetrieveUpdateAPIView):
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
