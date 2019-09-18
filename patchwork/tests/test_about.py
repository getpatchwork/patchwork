# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class AboutViewTest(TestCase):

    def _test_redirect(self, view):
        requested_url = reverse(view)
        redirect_url = reverse('about')

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url, 301)

    def test_redirects(self):
        for view in ['help', 'help-about']:
            self._test_redirect(view)

    @unittest.skipUnless(settings.ENABLE_XMLRPC,
                         'requires xmlrpc interface (use the ENABLE_XMLRPC '
                         'setting)')
    def test_redirects_xmlrpc(self):
        self._test_redirect('help-pwclient')

    def test_xmlrpc(self):
        with self.settings(ENABLE_XMLRPC=False):
            response = self.client.get(reverse('about'))
            self.assertFalse(response.context['enabled_apis']['xmlrpc'])

        with self.settings(ENABLE_XMLRPC=True):
            response = self.client.get(reverse('about'))
            self.assertTrue(response.context['enabled_apis']['xmlrpc'])

    def test_rest(self):
        with self.settings(ENABLE_REST_API=False):
            response = self.client.get(reverse('about'))
            self.assertFalse(response.context['enabled_apis']['rest'])

        with self.settings(ENABLE_REST_API=True):
            response = self.client.get(reverse('about'))
            self.assertTrue(response.context['enabled_apis']['rest'])
