# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render
from django.urls import reverse


def about(request):
    context = {
        'enabled_apis': {
            'rest': settings.ENABLE_REST_API,
            'xmlrpc': settings.ENABLE_XMLRPC,
        },
        'admins': () if settings.ADMINS_HIDE else settings.ADMINS,
    }

    return render(request, 'patchwork/about.html', context)


def redirect(request):
    """Redirect for legacy URLs.

    Remove this when Patchwork 3.0 is released.
    """
    return HttpResponsePermanentRedirect(reverse('about'))
