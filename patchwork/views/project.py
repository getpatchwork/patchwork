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

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.models import Project

from django.db import connection


def project_list(request):
    projects = Project.objects.all()

    if projects.count() == 1:
        return HttpResponseRedirect(
            reverse('patch-list',
                    kwargs={'project_id': projects[0].linkname}))

    context = {
        'projects': projects,
    }
    return render(request, 'patchwork/projects.html', context)


def project_detail(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)

    # So, we revert to raw sql because if we do what you'd think would
    # be the correct thing in Django-ese, it ends up doing a *pointless*
    # join with patchwork_submissions that ends up ruining the query.
    # So, we do not do this, as this is wrong:
    #
    #   patches = Patch.objects.filter(
    #       patch_project_id=project.id).only('archived')
    #   patches = patches.annotate(c=Count('archived'))
    #
    # and instead do this, because it's simple and fast

    n_patches = {}
    with connection.cursor() as cursor:
        cursor.execute('SELECT archived,COUNT(submission_ptr_id) as c '
                       'FROM patchwork_patch '
                       'WHERE patch_project_id=%s GROUP BY archived',
                       [project.id])

        for r in cursor:
            n_patches[r[0]] = r[1]

    context = {
        'project': project,
        'maintainers': User.objects.filter(
            profile__maintainer_projects=project),
        'n_patches': n_patches[False] if False in n_patches else 0,
        'n_archived_patches': n_patches[True] if True in n_patches else 0,
        'enable_xmlrpc': settings.ENABLE_XMLRPC,
    }
    return render(request, 'patchwork/project.html', context)
