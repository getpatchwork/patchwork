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

import json

from patchwork.models import Patch, Project, Person, EmailConfirmation
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from patchwork.requestcontext import PatchworkRequestContext
from django.core import urlresolvers
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q

def projects(request):
    context = PatchworkRequestContext(request)
    projects = Project.objects.all()

    if projects.count() == 1:
        return HttpResponseRedirect(
                urlresolvers.reverse('patchwork.views.patch.list',
                    kwargs = {'project_id': projects[0].linkname}))

    context['projects'] = projects
    return render_to_response('patchwork/projects.html', context)

def pwclientrc(request, project_id):
    project = get_object_or_404(Project, linkname = project_id)
    context = PatchworkRequestContext(request)
    context.project = project
    if settings.FORCE_HTTPS_LINKS or request.is_secure():
        context['scheme'] = 'https'
    else:
        context['scheme'] = 'http'
    response = HttpResponse(content_type = "text/plain")
    response['Content-Disposition'] = 'attachment; filename=.pwclientrc'
    response.write(render_to_string('patchwork/pwclientrc', context))
    return response

def pwclient(request):
    context = PatchworkRequestContext(request)
    response = HttpResponse(content_type = "text/x-python")
    response['Content-Disposition'] = 'attachment; filename=pwclient'
    response.write(render_to_string('patchwork/pwclient', context))
    return response

def confirm(request, key):
    import patchwork.views.user, patchwork.views.mail
    views = {
        'userperson': patchwork.views.user.link_confirm,
        'registration': patchwork.views.user.register_confirm,
        'optout': patchwork.views.mail.optout_confirm,
        'optin': patchwork.views.mail.optin_confirm,
    }

    conf = get_object_or_404(EmailConfirmation, key = key)
    if conf.type not in views:
        raise Http404

    if conf.active and conf.is_valid():
        return views[conf.type](request, conf)

    context = PatchworkRequestContext(request)
    context['conf'] = conf
    if not conf.active:
        context['error'] = 'inactive'
    elif not conf.is_valid():
        context['error'] = 'expired'

    return render_to_response('patchwork/confirm-error.html', context)

def submitter_complete(request):
    search = request.GET.get('q', '')
    limit = request.GET.get('l', None)

    if len(search) <= 3:
        return HttpResponse(content_type="application/json")

    queryset = Person.objects.filter(Q(name__icontains = search) |
                                     Q(email__icontains = search))
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            limit = None

    if limit is not None and limit > 0:
            queryset = queryset[:limit]

    data = []
    for submitter in queryset:
        item = {}
        item['pk'] = submitter.id
        item['name'] = submitter.name
        item['email'] = submitter.email
        data.append(item)

    return HttpResponse(json.dumps(data), content_type="application/json")

help_pages = {'':           'index.html',
              'about/':     'about.html',
             }

if settings.ENABLE_XMLRPC:
    help_pages['pwclient/'] = 'pwclient.html'

def help(request, path):
    context = PatchworkRequestContext(request)
    if path in help_pages:
        return render_to_response('patchwork/help/' + help_pages[path], context)
    raise Http404

