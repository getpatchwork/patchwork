# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.serializers import CharField

from patchwork.api.base import BaseHyperlinkedModelSerializer
from patchwork.api.base import PatchworkPermission
from patchwork.api.embedded import UserProfileSerializer
from patchwork.models import Project


class ProjectSerializer(BaseHyperlinkedModelSerializer):

    link_name = CharField(max_length=255, source='linkname', read_only=True)
    list_id = CharField(max_length=255, source='listid', read_only=True)
    list_email = CharField(max_length=200, source='listemail', read_only=True)
    maintainers = UserProfileSerializer(many=True, read_only=True,
                                        source='maintainer_project')

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'link_name', 'list_id', 'list_email',
                  'web_url', 'scm_url', 'webscm_url', 'maintainers',
                  'subject_match', 'list_archive_url',
                  'list_archive_url_format', 'commit_url_format')
        read_only_fields = ('name', 'link_name', 'list_id', 'list_email',
                            'maintainers', 'subject_match')
        versioned_fields = {
            '1.1': ('subject_match', ),
            '1.2': ('list_archive_url', 'list_archive_url_format',
                    'commit_url_format'),
        }
        extra_kwargs = {
            'url': {'view_name': 'api-project-detail'},
        }


class ProjectMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = ProjectSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        assert 'pk' in self.kwargs

        try:
            obj = queryset.get(id=int(self.kwargs['pk']))
        except (ValueError, Project.DoesNotExist):
            obj = get_object_or_404(queryset, linkname=self.kwargs['pk'])

        # NOTE(stephenfin): We must do this to make sure the 'url'
        # field is populated correctly
        self.kwargs['pk'] = obj.id

        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        return Project.objects.all().prefetch_related('maintainer_project')


class ProjectList(ProjectMixin, ListAPIView):
    """List projects."""

    search_fields = ('link_name', 'list_id', 'list_email', 'web_url',
                     'scm_url', 'webscm_url', 'list_archive_url',
                     'list_archive_url_format', 'commit_url_format')
    ordering_fields = ('id', 'name', 'link_name', 'list_id')
    ordering = 'id'


class ProjectDetail(ProjectMixin, RetrieveUpdateAPIView):
    """
    get:
    Show a project.

    patch:
    Update a project.

    put:
    Update a project.
    """

    pass
