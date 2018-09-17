# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
