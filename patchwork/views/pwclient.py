# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy

from patchwork.models import Project


def pwclientrc(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)

    if settings.FORCE_HTTPS_LINKS or request.is_secure():
        api_scheme = 'https'
    else:
        api_scheme = 'http'

    if settings.ENABLE_REST_API:
        api_backend = 'rest'
        api_path = reverse_lazy('api-index')
    else:
        api_backend = 'xmlrpc'
        api_path = reverse_lazy('xmlrpc')

    context = {
        'project': project,
        'api_backend': api_backend,
        'api_path': api_path,
        'api_scheme': api_scheme,
    }

    response = render(
        request,
        'patchwork/pwclientrc',
        context,
        content_type='text/plain',
    )
    response['Content-Disposition'] = 'attachment; filename=.pwclientrc'

    return response
