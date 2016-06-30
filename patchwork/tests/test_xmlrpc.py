# Patchwork - automated patch tracking system
# Copyright (C) 2014 Jeremy Kerr <jk@ozlabs.org>
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

import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.utils.six.moves import xmlrpc_client

from patchwork.tests.utils import create_patches


@unittest.skipUnless(settings.ENABLE_XMLRPC,
                     'requires xmlrpc interface (use the ENABLE_XMLRPC '
                     'setting)')
class XMLRPCTest(LiveServerTestCase):

    def setUp(self):
        self.url = self.live_server_url + reverse('xmlrpc')
        self.rpc = xmlrpc_client.Server(self.url)

    def test_get_redirect(self):
        response = self.client.patch(self.url)
        self.assertRedirects(
            response, reverse('help', kwargs={'path': 'pwclient/'}))

    def test_list_single(self):
        patch_objs = create_patches()
        patches = self.rpc.patch_list()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_objs[0].id)

    def test_list_multiple(self):
        create_patches(5)
        patches = self.rpc.patch_list()
        self.assertEqual(len(patches), 5)

    def test_list_max_count(self):
        patch_objs = create_patches(5)
        patches = self.rpc.patch_list({'max_count': 2})
        self.assertEqual(len(patches), 2)
        self.assertEqual(patches[0]['id'], patch_objs[0].id)

    def test_list_negative_max_count(self):
        patch_objs = create_patches(5)
        patches = self.rpc.patch_list({'max_count': -1})
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_objs[-1].id)
