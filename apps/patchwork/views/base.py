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


from patchwork.models import Patch, Project, Person, RegistrationRequest
from patchwork.filters import Filters
from patchwork.forms import RegisterForm, LoginForm, PatchForm
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import django.core.urlresolvers
from patchwork.requestcontext import PatchworkRequestContext
from django.core import serializers

def projects(request):
    context = PatchworkRequestContext(request)
    projects = Project.objects.all()

    if projects.count() == 1:
        return HttpResponseRedirect(
                django.core.urlresolvers.reverse('patchwork.views.patch.list',
                    kwargs = {'project_id': projects[0].linkname}))

    context['projects'] = projects
    return render_to_response('patchwork/projects.html', context)

def project(request, project_id):
    context = PatchworkRequestContext(request)
    project = get_object_or_404(Project, linkname = project_id)
    context.project = project

    context['maintainers'] = User.objects.filter( \
            userprofile__maintainer_projects = project)
    context['n_patches'] = Patch.objects.filter(project = project,
            archived = False).count()
    context['n_archived_patches'] = Patch.objects.filter(project = project,
            archived = True).count()

    return render_to_response('patchwork/project.html', context)

def submitter_complete(request):
    search = request.GET.get('q', '')
    response = HttpResponse(mimetype = "text/plain")
    if len(search) > 3:
	queryset = Person.objects.filter(name__icontains = search)
	json_serializer = serializers.get_serializer("json")()
	json_serializer.serialize(queryset, ensure_ascii=False, stream=response)
    return response
