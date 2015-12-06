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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from patchwork.models import Project
from patchwork.requestcontext import PatchworkRequestContext


def pwclientrc(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    context = PatchworkRequestContext(request)
    context.project = project
    if settings.FORCE_HTTPS_LINKS or request.is_secure():
        context['scheme'] = 'https'
    else:
        context['scheme'] = 'http'
    response = HttpResponse(content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename=.pwclientrc'
    response.write(render_to_string('patchwork/pwclientrc', context))
    return response


def pwclient(request):
    context = PatchworkRequestContext(request)
    response = HttpResponse(content_type="text/x-python")
    response['Content-Disposition'] = 'attachment; filename=pwclient'
    response.write(render_to_string('patchwork/pwclient', context))
    return response
