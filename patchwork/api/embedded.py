# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Serializers for embedded use.

A collection of serializers. None of the serializers here should reference
nested fields.
"""

from rest_framework.serializers import CharField
from rest_framework.serializers import SerializerMethodField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import CheckHyperlinkedIdentityField
from patchwork import models


class MboxMixin(BaseHyperlinkedModelSerializer):
    """Embed a link to the mbox URL.

    This field is just way too useful to leave out of even the embedded
    serialization.
    """

    mbox = SerializerMethodField()

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())


class WebURLMixin(BaseHyperlinkedModelSerializer):
    """Embed a link to the web URL."""

    web_url = SerializerMethodField()

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())


class BundleSerializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.Bundle
        fields = ('id', 'url', 'web_url', 'name', 'mbox')
        read_only_fields = fields
        versioned_field = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-bundle-detail'},
        }


class CheckSerializer(BaseHyperlinkedModelSerializer):

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


class CoverLetterSerializer(MboxMixin, WebURLMixin,
                            BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.CoverLetter
        fields = ('id', 'url', 'web_url', 'msgid', 'date', 'name', 'mbox')
        read_only_fields = fields
        versioned_field = {
            '1.1': ('web_url', 'mbox', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-cover-detail'},
        }


class PatchSerializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.Patch
        fields = ('id', 'url', 'web_url', 'msgid', 'date', 'name', 'mbox')
        read_only_fields = fields
        versioned_field = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-patch-detail'},
        }


class PersonSerializer(BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.Person
        fields = ('id', 'url', 'name', 'email')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-person-detail'},
        }


class ProjectSerializer(BaseHyperlinkedModelSerializer):

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


class SeriesSerializer(MboxMixin, WebURLMixin,
                       BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.Series
        fields = ('id', 'url', 'date', 'name', 'version', 'mbox')
        read_only_fields = fields
        versioned_field = {
            '1.1': ('web_url', ),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-series-detail'},
        }


class UserSerializer(BaseHyperlinkedModelSerializer):

    class Meta:
        model = models.User
        fields = ('id', 'url', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = fields
        extra_kwargs = {
            'url': {'view_name': 'api-user-detail'},
        }


class UserProfileSerializer(BaseHyperlinkedModelSerializer):

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
