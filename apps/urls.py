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
from patchwork.admin import admin_site

from registration.views import register
from patchwork.forms import RegistrationForm
from patchwork.utils import userprofile_register_callback

urlpatterns = patterns('',
    # Example:
    (r'^', include('patchwork.urls')),

    # override the default registration form
    url(r'^accounts/register/$',
        register,
        {'form_class': RegistrationForm,
         'profile_callback': userprofile_register_callback},
        name='registration_register'),

    (r'^accounts/', include('registration.urls')),

    # Uncomment this for admin:
     (r'^admin/(.*)', admin_site.root),

     (r'^css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': '/srv/patchwork/htdocs/css'}),
     (r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': '/srv/patchwork/htdocs/js'}),
     (r'^images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': '/srv/patchwork/htdocs/images'}),
)

if settings.ENABLE_XMLRPC:
    urlpatterns += patterns('',
		    (r'xmlrpc/$', 'django_xmlrpc.views.handle_xmlrpc'),
    )
