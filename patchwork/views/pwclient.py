# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.models import Project


def pwclientrc(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)

    context = {
        'project': project,
    }
    if settings.FORCE_HTTPS_LINKS or request.is_secure():
        context['scheme'] = 'https'
    else:
        context['scheme'] = 'http'

    response = render(request, 'patchwork/pwclientrc', context,
                      content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=.pwclientrc'

    return response
