# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from django.utils.translation import ugettext_lazy as _
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.relations import RelatedField
from rest_framework.reverse import reverse
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import ValidationError

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.filters import PatchFilterSet
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.models import Patch
from patchwork.models import State
from patchwork.parser import clean_subject


class StateField(RelatedField):
    """Avoid the need for a state endpoint.

    NOTE(stephenfin): This field will only function for State names consisting
    of alphanumeric characters, underscores and single spaces. In Patchwork
    2.0+, we should consider adding a slug field to the State object and make
    use of the SlugRelatedField in DRF.
    """
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid_choice': _('Invalid state {name}. Expected one of: '
                            '{choices}.'),
        'incorrect_type': _('Incorrect type. Expected string value, received '
                            '{data_type}.'),
    }

    @staticmethod
    def format_state_name(state):
        return ' '.join(state.split('-'))

    def to_internal_value(self, data):
        try:
            data = self.format_state_name(data)
            return self.get_queryset().get(name__iexact=data)
        except State.DoesNotExist:
            self.fail('invalid_choice', name=data, choices=', '.join([
                self.format_state_name(x.name) for x in self.get_queryset()]))
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, obj):
        return obj.slug

    def get_queryset(self):
        return State.objects.all()


class PatchListSerializer(BaseHyperlinkedModelSerializer):

    web_url = SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    state = StateField()
    submitter = PersonSerializer(read_only=True)
    delegate = UserSerializer(allow_null=True)
    mbox = SerializerMethodField()
    series = SeriesSerializer(read_only=True)
    comments = SerializerMethodField()
    check = SerializerMethodField()
    checks = SerializerMethodField()
    tags = SerializerMethodField()

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def get_comments(self, patch):
        return self.context.get('request').build_absolute_uri(
            reverse('api-patch-comment-list', kwargs={'pk': patch.id}))

    def get_check(self, instance):
        return instance.combined_check_state

    def get_checks(self, instance):
        return self.context.get('request').build_absolute_uri(
            reverse('api-check-list', kwargs={'patch_id': instance.id}))

    def get_tags(self, instance):
        # TODO(stephenfin): Make tags performant, possibly by reworking the
        # model
        return {}

    def validate_delegate(self, value):
        """Check that the delgate is a maintainer of the patch's project."""
        if not value:
            return value

        if not self.instance.project.maintainer_project.filter(
                id=value.id).exists():
            raise ValidationError("User '%s' is not a maintainer for project "
                                  "'%s'" % (value, self.instance.project))
        return value

    def to_representation(self, instance):
        # NOTE(stephenfin): This is here to ensure our API looks the same even
        # after we changed the series-patch relationship from M:N to 1:N. It
        # will be removed in API v2
        data = super(PatchListSerializer, self).to_representation(instance)
        data['series'] = [data['series']] if data['series'] else []
        return data

    class Meta:
        model = Patch
        fields = ('id', 'url', 'web_url', 'project', 'msgid',
                  'list_archive_url', 'date', 'name', 'commit_ref', 'pull_url',
                  'state', 'archived', 'hash', 'submitter', 'delegate', 'mbox',
                  'series', 'comments', 'check', 'checks', 'tags')
        read_only_fields = ('web_url', 'project', 'msgid', 'list_archive_url',
                            'date', 'name', 'hash', 'submitter', 'mbox',
                            'series', 'comments', 'check', 'checks', 'tags')
        versioned_fields = {
            '1.1': ('comments', 'web_url'),
            '1.2': ('list_archive_url',),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-patch-detail'},
        }


class PatchDetailSerializer(PatchListSerializer):

    headers = SerializerMethodField()
    prefixes = SerializerMethodField()

    def get_headers(self, patch):
        headers = {}

        if patch.headers:
            parsed = email.parser.Parser().parsestr(patch.headers, True)
            for key in parsed.keys():
                headers[key] = parsed.get_all(key)
                # Let's return a single string instead of a list if only one
                # header with this key is present
                if len(headers[key]) == 1:
                    headers[key] = headers[key][0]

        return headers

    def get_prefixes(self, instance):
        return clean_subject(instance.name)[1]

    class Meta:
        model = Patch
        fields = PatchListSerializer.Meta.fields + (
            'headers', 'content', 'diff', 'prefixes')
        read_only_fields = PatchListSerializer.Meta.read_only_fields + (
            'headers', 'content', 'diff', 'prefixes')
        versioned_fields = PatchListSerializer.Meta.versioned_fields
        extra_kwargs = PatchListSerializer.Meta.extra_kwargs


class PatchList(ListAPIView):
    """List patches."""

    permission_classes = (PatchworkPermission,)
    serializer_class = PatchListSerializer
    filter_class = filterset_class = PatchFilterSet
    search_fields = ('name',)
    ordering_fields = ('id', 'name', 'project', 'date', 'state', 'archived',
                       'submitter', 'check')
    ordering = 'id'

    def get_queryset(self):
        return Patch.objects.all()\
            .prefetch_related('check_set')\
            .select_related('project', 'state', 'submitter', 'delegate',
                            'series')\
            .defer('content', 'diff', 'headers')


class PatchDetail(RetrieveUpdateAPIView):
    """
    get:
    Show a patch.

    patch:
    Update a patch.

    put:
    Update a patch.
    """
    permission_classes = (PatchworkPermission,)
    serializer_class = PatchDetailSerializer

    def get_queryset(self):
        return Patch.objects.all()\
            .prefetch_related('check_set')\
            .select_related('project', 'state', 'submitter', 'delegate',
                            'series')
