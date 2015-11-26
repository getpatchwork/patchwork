# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
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

from __future__ import absolute_import

from django.conf import settings
from django.contrib.sites.models import Site
from django.template import RequestContext
from django.utils.html import escape

from patchwork.filters import Filters
from patchwork.models import Bundle, Project


def bundle(request):
    user = request.user
    if not user.is_authenticated():
        return {}
    return {'bundles': Bundle.objects.filter(owner=user)}


class PatchworkRequestContext(RequestContext):

    def __init__(self, request, project=None,
                 dict=None, processors=None,
                 list_view=None, list_view_params={}):
        self._project = project
        self.filters = Filters(request)
        if processors is None:
            processors = []
        processors.append(bundle)
        super(PatchworkRequestContext, self).__init__(
            request, dict, processors)

        self.update({
            'filters': self.filters,
            'messages': [],
        })
        if list_view:
            params = self.filters.params()
            for param in ['order', 'page']:
                data = {}
                if request.method == 'GET':
                    data = request.GET
                elif request.method == 'POST':
                    data = request.POST

                value = data.get(param, None)
                if value:
                    params.append((param, value))
            self.update({
                'list_view': {
                        'view': list_view,
                        'view_params': list_view_params,
                        'params': params
                        }})

        self.projects = Project.objects.all()

        self.update({
            'project': self.project,
            'site': Site.objects.get_current(),
            'settings': settings,
            'other_projects': len(self.projects) > 1
        })

    def _set_project(self, project):
        self._project = project
        self.filters.set_project(project)
        self.update({'project': self._project})

    def _get_project(self):
        return self._project

    project = property(_get_project, _set_project)

    def add_message(self, message):
        self['messages'].append(message)
