# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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

"""Serializers for embedded use.

A collection of serializers. None of the serializers here should reference
nested fields.
"""

from rest_framework.serializers import CharField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import CheckHyperlinkedIdentityField
from patchwork import models


class MboxMixin(HyperlinkedModelSerializer):
    """Embed an link to the mbox URL.

    This field is just way too useful to leave out of even the embedded
    serialization.
    """

    mbox = SerializerMethodField()

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())


class BundleSerializer(MboxMixin, HyperlinkedModelSerializer):

    class Meta:
        model = models.Bundle
        fields = ('id', 'url', 'name', 'mbox')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-bundle-detail'},
        }


class CheckSerializer(HyperlinkedModelSerializer):

    url = CheckHyperlinkedIdentityField('api-check-detail')

    def to_representation(self, instance):
        data = super(CheckSerializer, self).to_representation(instance)
        data['state'] = instance.get_state_display()
        return data

    class Meta:
        model = models.Check
        fields = ('id', 'url', 'date', 'state', 'target_url', 'context')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-check-detail'},

        }


class CoverLetterSerializer(MboxMixin, HyperlinkedModelSerializer):

    class Meta:
        model = models.CoverLetter
        fields = ('id', 'url', 'msgid', 'date', 'name', 'mbox')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-cover-detail'},
        }


class PatchSerializer(MboxMixin, HyperlinkedModelSerializer):

    class Meta:
        model = models.Patch
        fields = ('id', 'url', 'msgid', 'date', 'name', 'mbox')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-patch-detail'},
        }


class PersonSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = models.Person
        fields = ('id', 'url', 'name', 'email')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-person-detail'},
        }


class ProjectSerializer(HyperlinkedModelSerializer):

    link_name = CharField(max_length=255, source='linkname')
    list_id = CharField(max_length=255, source='listid')
    list_email = CharField(max_length=200, source='listemail')

    class Meta:
        model = models.Project
        fields = ('id', 'url', 'name', 'link_name', 'list_id', 'list_email',
                  'web_url', 'scm_url', 'webscm_url')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-project-detail'},
        }


class SeriesSerializer(MboxMixin, HyperlinkedModelSerializer):

    class Meta:
        model = models.Series
        fields = ('id', 'url', 'date', 'name', 'version', 'mbox')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
        }


class UserSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = models.User
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-user-detail'},
        }


class UserProfileSerializer(HyperlinkedModelSerializer):

    username = CharField(source='user.username')
    first_name = CharField(source='user.first_name')
    last_name = CharField(source='user.last_name')
    email = CharField(source='user.email')

    class Meta:
        model = models.UserProfile
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-user-detail'},
        }
