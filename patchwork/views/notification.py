# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

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

    try:
        conf = EmailConfirmation.objects.get(key=key)
    except EmailConfirmation.DoesNotExist:
        messages.error(
            request,
            'That request is invalid or expired. Please try again.'
        )
        return HttpResponseRedirect(reverse('project-list'))

    if conf.type not in views:
        messages.error(
            request,
            'That request is invalid or expired. Please try again.'
        )
        return HttpResponseRedirect(reverse('project-list'))

    if conf.active and conf.is_valid():
        return views[conf.type](request, conf)

    messages.error(
        request,
        'That request is invalid or expired. Please try again.'
    )
    return HttpResponseRedirect(reverse('project-list'))
