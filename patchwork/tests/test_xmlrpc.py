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
import xmlrpclib
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from patchwork.models import Person, Patch
from patchwork.tests.utils import defaults

@unittest.skipUnless(settings.ENABLE_XMLRPC,
        "requires xmlrpc interface (use the ENABLE_XMLRPC setting)")
class XMLRPCTest(LiveServerTestCase):
    fixtures = ['default_states']

    def setUp(self):
        settings.STATIC_URL = '/'
        self.url = (self.live_server_url +
                    reverse('patchwork.views.xmlrpc.xmlrpc'))
        self.rpc = xmlrpclib.Server(self.url)

    def testGetRedirect(self):
        response = self.client.get(self.url)
        self.assertRedirects(response,
                reverse('patchwork.views.help',
                    kwargs = {'path': 'pwclient/'}))

    def testList(self):
        defaults.project.save()
        defaults.patch_author_person.save()
        patch = Patch(project = defaults.project,
                submitter = defaults.patch_author_person,
                msgid = defaults.patch_name,
                content = defaults.patch)
        patch.save()

        patches = self.rpc.patch_list()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]['id'], patch.id)
