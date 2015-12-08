# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
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

from django.contrib.auth.models import User
from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from patchwork.models import Patch, Project
from patchwork.requestcontext import PatchworkRequestContext


def list(request):
    context = PatchworkRequestContext(request)
    projects = Project.objects.all()

    if projects.count() == 1:
        return HttpResponseRedirect(
            urlresolvers.reverse('patch-list',
                                 kwargs={'project_id': projects[0].linkname}))

    context['projects'] = projects

    return render_to_response('patchwork/projects.html', context)


def project(request, project_id):
    context = PatchworkRequestContext(request)
    project = get_object_or_404(Project, linkname=project_id)
    context.project = project

    context['maintainers'] = User.objects.filter(
        profile__maintainer_projects=project)
    context['n_patches'] = Patch.objects.filter(project=project,
                                                archived=False).count()
    context['n_archived_patches'] = Patch.objects.filter(project=project,
                                                         archived=True).count()

    return render_to_response('patchwork/project.html', context)
