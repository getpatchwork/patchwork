# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
# Copyright (C) 2019, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
# Copyright (C) 2020, IBM Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.relations import RelatedField
from rest_framework.reverse import reverse
from rest_framework.serializers import SerializerMethodField
from rest_framework import status

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.embedded import PatchSerializer
from patchwork.api.embedded import PersonSerializer
from patchwork.api.embedded import ProjectSerializer
from patchwork.api.embedded import SeriesSerializer
from patchwork.api.embedded import UserSerializer
from patchwork.api.filters import PatchFilterSet
from patchwork.models import Patch
from patchwork.models import PatchRelation
from patchwork.models import State
from patchwork.parser import clean_subject


class StateField(RelatedField):
    """Avoid the need for a state endpoint.

    TODO(stephenfin): Consider switching to SlugRelatedField for the v2.0 API.
    """
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid_choice': _('Invalid state {name}. Expected one of: '
                            '{choices}.'),
        'incorrect_type': _('Incorrect type. Expected string value, received '
                            '{data_type}.'),
    }

    def to_internal_value(self, data):
        data = slugify(data.lower())
        try:
            return self.get_queryset().get(slug=data)
        except State.DoesNotExist:
            self.fail('invalid_choice', name=data, choices=', '.join([
                x.slug for x in self.get_queryset()]))

    def to_representation(self, obj):
        return obj.slug

    def get_queryset(self):
        return State.objects.all()


class PatchConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        'At least one patch is already part of another relation. You have to '
        'explicitly remove a patch from its existing relation before moving '
        'it to this one.'
    )


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
    related = PatchSerializer(
        source='related.patches', many=True, default=[],
        style={'base_template': 'input.html'})

    def get_web_url(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_absolute_url())

    def get_mbox(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_mbox_url())

    def get_comments(self, patch):
        return self.context.get('request').build_absolute_uri(
            reverse('api-patch-comment-list', kwargs={'patch_id': patch.id}))

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

        if not value.profile.maintainer_projects.only('id').filter(
                id=self.instance.project.id).exists():
            raise ValidationError("User '%s' is not a maintainer for project "
                                  "'%s'" % (value, self.instance.project))
        return value

    def to_representation(self, instance):
        # NOTE(stephenfin): This is here to ensure our API looks the same even
        # after we changed the series-patch relationship from M:N to 1:N. It
        # will be removed in API v2
        data = super(PatchListSerializer, self).to_representation(instance)
        data['series'] = [data['series']] if data['series'] else []

        # Remove this patch from 'related'
        if 'related' in data and data['related']:
            data['related'] = [
                x for x in data['related'] if x['id'] != data['id']
            ]

        return data

    class Meta:
        model = Patch
        fields = ('id', 'url', 'web_url', 'project', 'msgid',
                  'list_archive_url', 'date', 'name', 'commit_ref', 'pull_url',
                  'state', 'archived', 'hash', 'submitter', 'delegate', 'mbox',
                  'series', 'comments', 'check', 'checks', 'tags', 'related',)
        read_only_fields = ('web_url', 'project', 'msgid', 'list_archive_url',
                            'date', 'name', 'hash', 'submitter', 'mbox',
                            'series', 'comments', 'check', 'checks', 'tags')
        versioned_fields = {
            '1.1': ('comments', 'web_url'),
            '1.2': ('list_archive_url', 'related',),
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

    def update(self, instance, validated_data):
        # d-r-f cannot handle writable nested models, so we handle that
        # specifically ourselves and let d-r-f handle the rest
        if 'related' not in validated_data:
            return super(PatchDetailSerializer, self).update(
                instance, validated_data)

        related = validated_data.pop('related')

        # Validation rules
        # ----------------
        #
        # Permissions: to change a relation:
        #   for all patches in the relation, current and proposed,
        #     the user must be maintainer of the patch's project
        #  Note that this has a ratchet effect: if you add a cross-project
        #  relation, only you or another maintainer across both projects can
        #  modify that relationship in _any way_.
        #
        # Break before Make: a patch must be explicitly removed from a
        #   relation before being added to another
        #
        # No Read-Modify-Write for deletion:
        #   to delete a patch from a relation, clear _its_ related patch,
        #   don't modify one of the patches that are to remain.
        #
        # (As a consequence of those two, operations are additive:
        #   if 1 is in a relation with [1,2,3], then
        #   patching 1 with related=[2,4] gives related=[1,2,3,4])

        # Permissions:
        # Because we're in a serializer, not a view, this is a bit clunky
        user = self.context['request'].user.profile
        # Must be maintainer of:
        #  - current patch
        self.check_user_maintains_all(user, [instance])
        #  - all patches currently in relation
        #  - all patches proposed to be in relation
        patches = set(related['patches']) if related else {}
        if instance.related is not None:
            patches = patches.union(instance.related.patches.all())
        self.check_user_maintains_all(user, patches)

        # handle deletion
        if not related['patches']:
            # do not allow relations with a single patch
            if instance.related and instance.related.patches.count() == 2:
                instance.related.delete()
            instance.related = None
            return super(PatchDetailSerializer, self).update(
                instance, validated_data)

        # break before make
        relations = {patch.related for patch in patches if patch.related}
        if len(relations) > 1:
            raise PatchConflict()
        if relations:
            relation = relations.pop()
        else:
            relation = None
        if relation and instance.related is not None:
            if instance.related != relation:
                raise PatchConflict()

        # apply
        if relation is None:
            relation = PatchRelation()
            relation.save()
        for patch in patches:
            patch.related = relation
            patch.save()
        instance.related = relation
        instance.save()

        return super(PatchDetailSerializer, self).update(
            instance, validated_data)

    @staticmethod
    def check_user_maintains_all(user, patches):
        maintains = user.maintainer_projects.all()
        if any(s.project not in maintains for s in patches):
            detail = (
                'At least one patch is part of a project you are not '
                'maintaining.'
            )
            raise PermissionDenied(detail=detail)
        return True

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
        # TODO(dja): we need to revisit this after the patch migration, paying
        # particular attention to cases with filtering
        return Patch.objects.all()\
            .prefetch_related(
                'check_set', 'delegate', 'project', 'series__project',
                'related__patches__project')\
            .select_related('state', 'submitter', 'series')\
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
            .prefetch_related('check_set', 'related__patches__project')\
            .select_related('project', 'state', 'submitter', 'delegate',
                            'series')
