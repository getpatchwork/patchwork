# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

from rest_framework.serializers import CharField
from rest_framework.serializers import HyperlinkedModelSerializer

from patchwork.api.base import PatchworkPermission
from patchwork.api.base import PatchworkViewSet
from patchwork.models import Project


class ProjectSerializer(HyperlinkedModelSerializer):
    link_name = CharField(max_length=255, source='linkname')
    list_id = CharField(max_length=255, source='listid')
    list_email = CharField(max_length=200, source='listemail')

    class Meta:
        model = Project
        fields = ('url', 'name', 'link_name', 'list_id', 'list_email',
                  'web_url', 'scm_url', 'webscm_url')


class ProjectViewSet(PatchworkViewSet):
    permission_classes = (PatchworkPermission,)
    serializer_class = ProjectSerializer

    def _handle_linkname(self, pk):
        '''Make it easy for users to list by project-id or linkname'''
        qs = self.get_queryset()
        try:
            qs.get(id=pk)
        except (self.serializer_class.Meta.model.DoesNotExist, ValueError):
            # probably a non-numeric value which means we are going by linkname
            self.kwargs = {'linkname': pk}  # try and lookup by linkname
            self.lookup_field = 'linkname'

    def retrieve(self, request, pk=None):
        self._handle_linkname(pk)
        return super(ProjectViewSet, self).retrieve(request, pk)

    def partial_update(self, request, pk=None):
        self._handle_linkname(pk)
        return super(ProjectViewSet, self).partial_update(request, pk)
