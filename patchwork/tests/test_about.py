# Patchwork - automated patch tracking system
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

from django.test import TestCase
from django.urls import reverse


class AboutViewTest(TestCase):

    def test_redirects(self):
        for view in ['help', 'help-about', 'help-pwclient']:
            requested_url = reverse(view)
            redirect_url = reverse('about')

            response = self.client.get(requested_url)
            self.assertRedirects(response, redirect_url, 301)

    def test_xmlrpc(self):
        with self.settings(ENABLE_XMLRPC=False):
            response = self.client.get(reverse('about'))
            self.assertFalse(response.context['enabled_apis']['xmlrpc'])

        with self.settings(ENABLE_XMLRPC=True):
            response = self.client.get(reverse('about'))
            self.assertTrue(response.context['enabled_apis']['xmlrpc'])

    def test_rest(self):
        # TODO(stephenfin): There appears to be a bug in Django 1.10.x under
        # Python 3.5, meaning we can't use 'override_settings' here or we cause
        # the REST API tests to fail. We should investigate this.
        with self.settings(ENABLE_REST_API=False):
            response = self.client.get(reverse('about'))
            self.assertFalse(response.context['enabled_apis']['rest'])

        with self.settings(ENABLE_REST_API=True):
            response = self.client.get(reverse('about'))
            self.assertTrue(response.context['enabled_apis']['rest'])
