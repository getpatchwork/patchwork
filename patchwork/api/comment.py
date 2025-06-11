# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import get_object_or_404
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import SAFE_METHODS
from rest_framework.serializers import CreateOnlyDefault
from rest_framework.serializers import CharField
from rest_framework.serializers import HiddenField
from rest_framework.serializers import ValidationError
from rest_framework.serializers import SerializerMethodField
from rest_framework.views import PermissionDenied
from rest_framework.exceptions import NotAuthenticated
from django_filters.rest_framework import ChoiceFilter
from django_filters.rest_framework import FilterSet

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import CurrentCoverDefault
from patchwork.api.base import CurrentPersonDefault
from patchwork.api.base import NestedHyperlinkedIdentityField
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
        return (
            email.parser.Parser()
            .parsestr(comment.headers, True)
            .get('Subject', '')
        )

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
        fields = (
            'id',
            'url',
            'web_url',
            'msgid',
            'list_archive_url',
            'date',
            'subject',
            'submitter',
            'content',
            'headers',
            'addressed',
        )
        read_only_fields = (
            'id',
            'url',
            'web_url',
            'msgid',
            'list_archive_url',
            'date',
            'subject',
            'submitter',
            'content',
            'headers',
        )
        versioned_fields = {
            '1.1': ('web_url',),
            '1.2': ('list_archive_url',),
            '1.3': (
                'addressed',
                'url',
            ),
        }


class CoverCommentSerializer(BaseCommentListSerializer):
    url = NestedHyperlinkedIdentityField(
        'api-cover-comment-detail',
        lookup_field_mapping={
            'cover_id': 'cover_id',
            'comment_id': 'id',
        },
    )
    cover = HiddenField(default=CreateOnlyDefault(CurrentCoverDefault()))

    class Meta:
        model = CoverComment
        fields = BaseCommentListSerializer.Meta.fields + ('cover',)
        read_only_fields = BaseCommentListSerializer.Meta.read_only_fields + (
            'cover',
        )
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields
        extra_kwargs = {'url': {'view_name': 'api-cover-comment-detail'}}


class CoverMaintainerNoteSerializer(CoverCommentSerializer):
    content = CharField(required=True)
    submitter = PersonSerializer(
        read_only=True, default=CreateOnlyDefault(CurrentPersonDefault())
    )

    def validate(self, attrs):
        is_create = self.instance is None
        if is_create:
            # ReadOnly fields are ignored in create/update operations
            submitter_field = self.fields.get('submitter')
            attrs['submitter'] = submitter_field.default(submitter_field)

            if self.Meta.model.objects.filter(
                cover=attrs['cover'], msgid=''
            ).first():
                raise ValidationError(
                    'Maintaner note already exists for cover'
                )

        return super().validate(attrs)

    class Meta:
        model = CoverComment
        fields = CoverCommentSerializer.Meta.fields
        read_only_fields = tuple(
            f
            for f in CoverCommentSerializer.Meta.read_only_fields
            if f not in ('content',)
        )


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

        return CoverComment.objects.filter(cover=cover_id).select_related(
            'submitter'
        )


class PatchCommentSerializer(BaseCommentListSerializer):
    url = NestedHyperlinkedIdentityField(
        'api-patch-comment-detail',
        lookup_field_mapping={
            'patch_id': 'patch_id',
            'comment_id': 'id',
        },
    )
    patch = HiddenField(default=CreateOnlyDefault(CurrentPatchDefault()))

    class Meta:
        model = PatchComment
        fields = BaseCommentListSerializer.Meta.fields + ('patch',)
        read_only_fields = BaseCommentListSerializer.Meta.read_only_fields + (
            'patch',
        )
        versioned_fields = BaseCommentListSerializer.Meta.versioned_fields
        extra_kwargs = {'url': {'view_name': 'api-patch-comment-detail'}}


class PatchMaintainerNoteSerializer(PatchCommentSerializer):
    content = CharField(required=True)
    submitter = PersonSerializer(
        read_only=True, default=CreateOnlyDefault(CurrentPersonDefault())
    )

    def validate(self, attrs):
        is_create = self.instance is None
        if is_create:
            # ReadOnly fields are ignored in create/update operations
            submitter_field = self.fields.get('submitter')
            attrs['submitter'] = submitter_field.default(submitter_field)

            if self.Meta.model.objects.filter(
                patch=attrs['patch'], msgid=''
            ).first():
                raise ValidationError(
                    'Maintaner note already exists for patch'
                )

        return super().validate(attrs)

    class Meta:
        model = PatchComment
        fields = PatchCommentSerializer.Meta.fields
        read_only_fields = tuple(
            f
            for f in PatchCommentSerializer.Meta.read_only_fields
            if f not in ('content',)
        )


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

        return PatchComment.objects.filter(patch=patch_id).select_related(
            'submitter'
        )


COMMENT_TYPES = (
    ('comments', 'Comments'),
    ('notes', 'Maintainer Notes'),
)


class CommentsFilter(FilterSet):
    type = ChoiceFilter(
        label='Type',
        field_name='msgid',
        choices=COMMENT_TYPES,
        method='filter_choice',
    )

    def filter_choice(self, queryset, name, value):
        if name == 'msgid' and value == 'notes':
            return queryset.filter(msgid='')

        return queryset.exclude(msgid='')

    class Meta:
        fields = ['msgid']


class MaintainerNoteMixin(object):
    """
    Only maintainers can create objects and when creating or updating a note
    use the correct serializer.

    Override `maintainer_note_serializer_class` with the serializer that must
    be used and `project_lookup_attr` with the validated data key that holds a
    relationship with the object project.
    """

    maintainer_note_serializer_class = None
    project_lookup_attr = ''
    filterset_class = CommentsFilter
    _ERROR_MSG_MAP = {'DELETE': 'delete', 'POST': 'create'}

    def get_queryset(self):
        """
        We always remove maintainer notes from the queryset, unless specified
        by the filter type.
        """
        qs = super(MaintainerNoteMixin, self).get_queryset()
        if (
            self.request.method in SAFE_METHODS
            and not self.request.query_params.get('type')
        ):
            return qs.exclude(msgid='')
        return qs

    def get_serializer_class(self):
        assert self.maintainer_note_serializer_class is not None

        if self.request.method in ('PUT', 'PATCH'):
            obj = self.get_object()
            if obj and obj.is_maintainer_note:
                return self.maintainer_note_serializer_class

        if self.request.method == 'POST':
            return self.maintainer_note_serializer_class

        return super(MaintainerNoteMixin, self).get_serializer_class()

    def _check_notes_permission(self, instance, user):
        assert self.project_lookup_attr != ''
        try:
            project = instance[self.project_lookup_attr].project
            msgid = instance.get('msgid', '')
        except (TypeError, KeyError):
            project = getattr(instance, self.project_lookup_attr).project
            msgid = instance.msgid

        action_msg = self._ERROR_MSG_MAP[self.request.method]
        if not user or not user.is_authenticated:
            raise NotAuthenticated(
                f'You must be authenticated to {action_msg} a maintainer note'
            )

        if msgid:
            raise PermissionDenied(
                f'Only maintainer notes can be {action_msg}d'
            )
        if not project.is_editable(user):
            raise PermissionDenied(
                f'You must be a maintainer to {action_msg} a note'
            )

    def perform_create(self, serializer):
        self._check_notes_permission(
            serializer.validated_data, self.request.user
        )
        return super(MaintainerNoteMixin, self).perform_create(serializer)

    def perform_destroy(self, instance):
        self._check_notes_permission(instance, self.request.user)
        return super(MaintainerNoteMixin, self).perform_destroy(instance)


class CoverCommentList(
    MaintainerNoteMixin, CoverCommentMixin, ListCreateAPIView
):
    """
    get:
    List cover comments

    post:
    Create a maintainer note in the cover
    """

    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'cover_id'
    maintainer_note_serializer_class = CoverMaintainerNoteSerializer
    project_lookup_attr = 'cover'


class CoverCommentDetail(
    MaintainerNoteMixin,
    CoverCommentMixin,
    MultipleFieldLookupMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    get:
    Show a cover comment.

    patch:
    Update a cover comment or maintainer note.

    put:
    Update a cover comment or maintainer note.

    delete:
    Delete a maintainer note.
    """

    lookup_url_kwargs = ('cover_id', 'comment_id')
    lookup_fields = ('cover_id', 'id')
    maintainer_note_serializer_class = CoverMaintainerNoteSerializer
    project_lookup_attr = 'cover'


class PatchCommentList(
    MaintainerNoteMixin, PatchCommentMixin, ListCreateAPIView
):
    """
    get:
    List patch comments

    post:
    Create a maintainer note in the patch
    """

    search_fields = ('subject',)
    ordering_fields = ('id', 'subject', 'date', 'submitter')
    ordering = 'id'
    lookup_url_kwarg = 'patch_id'
    maintainer_note_serializer_class = PatchMaintainerNoteSerializer
    project_lookup_attr = 'patch'


class PatchCommentDetail(
    MaintainerNoteMixin,
    PatchCommentMixin,
    MultipleFieldLookupMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    get:
    Show a patch comment.

    patch:
    Update a patch comment or maintainer note.

    put:
    Update a patch comment or maintainer note.

    delete:
    Delete a maintainer note.
    """

    lookup_url_kwargs = ('patch_id', 'comment_id')
    lookup_fields = ('patch_id', 'id')
    maintainer_note_serializer_class = PatchMaintainerNoteSerializer
    project_lookup_attr = 'patch'
