# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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
    }

    return render(request, 'patchwork/about.html', context)


def redirect(request):
    """Redirect for legacy URLs.

    Remove this when Patchwork 3.0 is released.
    """
    return HttpResponsePermanentRedirect(reverse('about'))
