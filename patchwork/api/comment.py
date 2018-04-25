# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
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

from rest_framework.generics import ListAPIView
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.embedded import PersonSerializer
from patchwork.models import Comment


class CommentListSerializer(BaseHyperlinkedModelSerializer):

    subject = SerializerMethodField()
    headers = SerializerMethodField()
    submitter = PersonSerializer(read_only=True)

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
        fields = ('id', 'msgid', 'date', 'subject', 'submitter', 'content',
                  'headers')
        read_only_fields = fields


class CommentList(ListAPIView):
    """List comments"""

    permission_classes = (PatchworkPermission,)
    serializer_class = CommentListSerializer
    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Comment.objects.filter(
            submission=self.kwargs['pk']
        ).select_related('submitter')
