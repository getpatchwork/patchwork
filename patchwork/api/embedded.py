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

from collections import OrderedDict

from rest_framework.serializers import CharField
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import PrimaryKeyRelatedField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import CheckHyperlinkedIdentityField
from patchwork import models


class SerializedRelatedField(PrimaryKeyRelatedField):
    """
    A read-write field that expects a primary key for writes and returns a
    serialized version of the underlying field on reads.
    """

    def use_pk_only_optimization(self):
        # We're using embedded serializers so we want the whole object
        return False

    def get_queryset(self):
        return self._Serializer.Meta.model.objects.all()

    def get_choices(self, cutoff=None):
        # Override this so we don't call 'to_representation', which no longer
        # returns a flat value
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                item.pk,
                self.display_value(item)
            )
            for item in queryset
        ])

    def to_representation(self, data):
        return self._Serializer(context=self.context).to_representation(data)


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


class BundleSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

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


class CheckSerializer(SerializedRelatedField):

    class _Serializer(BaseHyperlinkedModelSerializer):

        url = CheckHyperlinkedIdentityField('api-check-detail')

        def to_representation(self, instance):
            data = super(CheckSerializer._Serializer, self).to_representation(
                instance)
            data['state'] = instance.get_state_display()
            return data

        class Meta:
            model = models.Check
            fields = ('id', 'url', 'date', 'state', 'target_url', 'context')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-check-detail'},
            }


class CoverLetterSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

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


class PatchSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

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


class PersonSerializer(SerializedRelatedField):

    class _Serializer(BaseHyperlinkedModelSerializer):

        class Meta:
            model = models.Person
            fields = ('id', 'url', 'name', 'email')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-person-detail'},
            }


class ProjectSerializer(SerializedRelatedField):

    class _Serializer(BaseHyperlinkedModelSerializer):

        link_name = CharField(max_length=255, source='linkname')
        list_id = CharField(max_length=255, source='listid')
        list_email = CharField(max_length=200, source='listemail')

        class Meta:
            model = models.Project
            fields = ('id', 'url', 'name', 'link_name', 'list_id',
                      'list_email', 'web_url', 'scm_url', 'webscm_url')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-project-detail'},
            }


class SeriesSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

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


class UserSerializer(SerializedRelatedField):

    class _Serializer(BaseHyperlinkedModelSerializer):

        class Meta:
            model = models.User
            fields = ('id', 'url', 'username', 'first_name', 'last_name',
                      'email')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-user-detail'},
            }


class UserProfileSerializer(SerializedRelatedField):

    class _Serializer(BaseHyperlinkedModelSerializer):

        username = CharField(source='user.username')
        first_name = CharField(source='user.first_name')
        last_name = CharField(source='user.last_name')
        email = CharField(source='user.email')

        class Meta:
            model = models.UserProfile
            fields = ('id', 'url', 'username', 'first_name', 'last_name',
                      'email')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-user-detail'},
            }
