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
from django.http import Http404
from django.shortcuts import render


help_pages = {
    '': 'index.html',
    'about/': 'about.html',
}

if settings.ENABLE_XMLRPC:
    help_pages['pwclient/'] = 'pwclient.html'


def help(request, path):
    if path in help_pages:
        return render(request,
                      'patchwork/help/' + help_pages[path])
    raise Http404
