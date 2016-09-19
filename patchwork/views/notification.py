# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
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

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.models import EmailConfirmation
from patchwork.views import mail
from patchwork.views import user


def confirm(request, key):

    views = {
        'userperson': user.link_confirm,
        'registration': user.register_confirm,
        'optout': mail.optout_confirm,
        'optin': mail.optin_confirm,
    }

    conf = get_object_or_404(EmailConfirmation, key=key)
    if conf.type not in views:
        raise Http404

    if conf.active and conf.is_valid():
        return views[conf.type](request, conf)

    context = {}
    context['conf'] = conf
    if not conf.active:
        context['error'] = 'inactive'
    elif not conf.is_valid():
        context['error'] = 'expired'

    return render(request, 'patchwork/confirm-error.html', context)
