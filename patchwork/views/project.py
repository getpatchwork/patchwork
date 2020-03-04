# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.models import Patch
from patchwork.models import Project


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
    patches = Patch.objects.filter(project=project)

    context = {
        'project': project,
        'maintainers': User.objects.filter(
            profile__maintainer_projects=project).select_related('profile'),
        'n_patches': patches.filter(archived=False).count(),
        'n_archived_patches': patches.filter(archived=True).count(),
        'enable_xmlrpc': settings.ENABLE_XMLRPC,
    }
    return render(request, 'patchwork/project.html', context)
