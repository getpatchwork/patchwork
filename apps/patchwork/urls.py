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

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    # Example:
    (r'^$', 'patchwork.views.projects'),
    (r'^project/(?P<project_id>[^/]+)/list/$', 'patchwork.views.patch.list'),
    (r'^project/(?P<project_id>[^/]+)/$', 'patchwork.views.project'),

    # patch views
    (r'^patch/(?P<patch_id>\d+)/$', 'patchwork.views.patch.patch'),
    (r'^patch/(?P<patch_id>\d+)/raw/$', 'patchwork.views.patch.content'),
    (r'^patch/(?P<patch_id>\d+)/mbox/$', 'patchwork.views.patch.mbox'),

    # logged-in user stuff
    (r'^user/$', 'patchwork.views.user.profile'),
    (r'^user/todo/$', 'patchwork.views.user.todo_lists'),
    (r'^user/todo/(?P<project_id>[^/]+)/$', 'patchwork.views.user.todo_list'),

    (r'^user/bundle/(?P<bundle_id>[^/]+)/$',
        'patchwork.views.bundle.bundle'),
    (r'^user/bundle/(?P<bundle_id>[^/]+)/mbox/$',
        'patchwork.views.bundle.mbox'),

    (r'^user/link/$', 'patchwork.views.user.link'),
    (r'^user/link/(?P<key>[^/]+)/$', 'patchwork.views.user.link_confirm'),
    (r'^user/unlink/(?P<person_id>[^/]+)/$', 'patchwork.views.user.unlink'),

    # public view for bundles
    (r'^bundle/(?P<username>[^/]*)/(?P<bundlename>[^/]*)/$',
                                'patchwork.views.bundle.public'),

    # submitter autocomplete
    (r'^submitter/$', 'patchwork.views.submitter_complete'),

    # help!
    (r'^help/(?P<path>.*)$', 'patchwork.views.help'),
)

if settings.ENABLE_XMLRPC:
    urlpatterns += patterns('',
        (r'xmlrpc/$', 'patchwork.views.xmlrpc.xmlrpc'),
        (r'^pwclient.py/$', 'patchwork.views.pwclient'),
        (r'^project/(?P<project_id>[^/]+)/pwclientrc/$',
             'patchwork.views.pwclientrc'),
    )
