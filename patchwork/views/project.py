# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from patchwork import forms
from patchwork.models import Patch
from patchwork.models import Project


def project_list(request):
    projects = Project.objects.all()

    if projects.count() == 1:
        return HttpResponseRedirect(
            reverse('patch-list', kwargs={'project_id': projects[0].linkname})
        )

    context = {
        'projects': projects,
    }
    return render(request, 'patchwork/projects.html', context)


def project_detail(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    patches = Patch.objects.filter(project=project)

    add_maintainer_form = forms.AddProjectMaintainerForm(project),
    remove_maintainer_form = forms.RemoveProjectMaintainerForm(project)
    project_settings_form = forms.ProjectSettingsForm(instance=project)

    if request.method == 'POST':
        form_name = request.POST.get('form_name', '')
        if form_name == forms.AddProjectMaintainerForm.name:
            add_maintainer_form = forms.AddProjectMaintainerForm(
                project, data=request.POST)
            if add_maintainer_form.is_valid():
                messages.success(
                    request,
                    'Added new maintainer.',
                )
                return HttpResponseRedirect(
                    reverse(
                        'project-detail',
                        kwargs={'project_id': project.linkname},
                    ),
                )
            messages.error(request, 'Error adding project maintainer.')
        elif form_name == forms.RemoveProjectMaintainerForm.name:
            remove_maintainer_form = forms.RemoveProjectMaintainerForm(
                project, data=request.POST)
            if remove_maintainer_form.is_valid():
                messages.success(
                    request,
                    'Removed maintainer.',
                )
                return HttpResponseRedirect(
                    reverse(
                        'project-detail',
                        kwargs={'project_id': project.linkname},
                    ),
                )
            messages.error(request, 'Error removing project maintainer.')
        elif form_name == forms.ProjectSettingsForm.name:
            project_settings_form = forms.ProjectSettingsForm(
                instance=project, data=request.POST)
            if project_settings_form.is_valid():
                project_settings_form.save()
                messages.success(
                    request,
                    'Updated project settings.',
                )
                return HttpResponseRedirect(
                    reverse(
                        'project-detail',
                        kwargs={'project_id': project.linkname},
                    ),
                )
            messages.error(request, 'Error updating project settings.')
        else:
            messages.error(request, 'Unrecognized request')

    context = {
        'project': project,
        'maintainers': User.objects.filter(
            profile__maintainer_projects=project
        ).select_related('profile'),
        'n_patches': patches.filter(archived=False).count(),
        'add_maintainer_form': add_maintainer_form,
        'remove_maintainer_form': remove_maintainer_form,
        'project_settings_form': project_settings_form,
    }

    if settings.ENABLE_XMLRPC:
        if settings.FORCE_HTTPS_LINKS or request.is_secure():
            scheme = 'https'
        else:
            scheme = 'http'

        context['pwclientrc'] = render_to_string(
            'patchwork/pwclientrc',
            {
                'project': project,
                'scheme': scheme,
                'user': request.user,
                'site': get_current_site(request),
            },
        ).strip()

    return render(request, 'patchwork/project.html', context)
