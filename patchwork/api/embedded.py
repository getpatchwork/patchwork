# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Serializers for embedded use.

A collection of serializers. None of the serializers here should reference
nested fields.
"""

from collections import OrderedDict

from rest_framework.serializers import CharField
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.serializers import SerializerMethodField

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


class CoverSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

        class Meta:
            model = models.Cover
            fields = ('id', 'url', 'web_url', 'msgid', 'list_archive_url',
                      'date', 'name', 'mbox')
            read_only_fields = fields
            versioned_fields = {
                '1.1': ('web_url', 'mbox', ),
                '1.2': ('list_archive_url',),
            }
            extra_kwargs = {
                'url': {'view_name': 'api-cover-detail'},
            }


class PatchSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

        class Meta:
            model = models.Patch
            fields = ('id', 'url', 'web_url', 'msgid', 'list_archive_url',
                      'date', 'name', 'mbox')
            read_only_fields = fields
            versioned_fields = {
                '1.1': ('web_url', ),
                '1.2': ('list_archive_url',),
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
                      'list_email', 'web_url', 'scm_url', 'webscm_url',
                      'list_archive_url', 'list_archive_url_format',
                      'commit_url_format')
            read_only_fields = fields
            extra_kwargs = {
                'url': {'view_name': 'api-project-detail'},
            }
            versioned_fields = {
                '1.2': ('list_archive_url', 'list_archive_url_format',
                        'commit_url_format'),
            }


class SeriesSerializer(SerializedRelatedField):

    class _Serializer(MboxMixin, WebURLMixin, BaseHyperlinkedModelSerializer):

        class Meta:
            model = models.Series
            fields = ('id', 'url', 'web_url', 'date', 'name', 'version',
                      'mbox')
            read_only_fields = fields
            versioned_fields = {
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
