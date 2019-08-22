# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from django.http import Http404
from rest_framework.generics import ListAPIView
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.embedded import PersonSerializer
from patchwork.models import Comment
from patchwork.models import Submission


class CommentListSerializer(BaseHyperlinkedModelSerializer):

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
        model = Comment
        fields = ('id', 'web_url', 'msgid', 'list_archive_url', 'date',
                  'subject', 'submitter', 'content', 'headers')
        read_only_fields = fields
        versioned_fields = {
            '1.1': ('web_url', ),
            '1.2': ('list_archive_url',),
        }


class CommentList(ListAPIView):
    """List comments"""

    permission_classes = (PatchworkPermission,)
    serializer_class = CommentListSerializer
    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        if not Submission.objects.filter(pk=self.kwargs['pk']).exists():
            raise Http404

        return Comment.objects.filter(
            submission=self.kwargs['pk']
        ).select_related('submitter')
