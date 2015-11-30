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

from email.utils import make_msgid
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.utils.six.moves import xmlrpc_client

from patchwork.models import Patch
from patchwork.tests.utils import defaults


@unittest.skipUnless(settings.ENABLE_XMLRPC,
                     'requires xmlrpc interface (use the ENABLE_XMLRPC '
                     'setting)')
class XMLRPCTest(LiveServerTestCase):
    fixtures = ['default_states']

    def setUp(self):
        self.url = (self.live_server_url + reverse('xmlrpc'))
        self.rpc = xmlrpc_client.Server(self.url)

    def testGetRedirect(self):
        response = self.client.patch(self.url)
        self.assertRedirects(response,
                             reverse('help', kwargs={'path': 'pwclient/'}))

    def _createPatches(self, count=1):
        defaults.project.save()
        defaults.patch_author_person.save()

        patches = []

        for _ in range(0, count):
            patch = Patch(project=defaults.project,
                          submitter=defaults.patch_author_person,
                          msgid=make_msgid(),
                          content=defaults.patch)
            patch.save()
            patches.append(patch)

        return patches

    def testListSingle(self):
        patch_objs = self._createPatches()
        patches = self.rpc.patch_list()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_objs[0].id)

    def testListMultiple(self):
        self._createPatches(5)
        patches = self.rpc.patch_list()
        self.assertEqual(len(patches), 5)

    def testListMaxCount(self):
        patch_objs = self._createPatches(5)
        patches = self.rpc.patch_list({'max_count': 2})
        self.assertEqual(len(patches), 2)
        self.assertEqual(patches[0]['id'], patch_objs[0].id)

    def testListNegativeMaxCount(self):
        patch_objs = self._createPatches(5)
        patches = self.rpc.patch_list({'max_count': -1})
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch_objs[-1].id)
