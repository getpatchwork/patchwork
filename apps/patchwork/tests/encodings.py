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

import unittest
import os
import time
from patchwork.models import Patch
from patchwork.tests.utils import defaults, read_patch
from django.test import TestCase
from django.test.client import Client

class UTF8PatchViewTest(TestCase):
    patch_filename = '0002-utf-8.patch'
    patch_encoding = 'utf-8'

    def setUp(self):
        defaults.project.save()
        defaults.patch_author_person.save()
        self.patch_content = read_patch(self.patch_filename,
                encoding = self.patch_encoding)
        self.patch = Patch(project = defaults.project,
                           msgid = 'x', name = defaults.patch_name,
                           submitter = defaults.patch_author_person,
                           content = self.patch_content)
        self.patch.save()
        self.client = Client()

    def testPatchView(self):
        response = self.client.get('/patch/%d/' % self.patch.id)
        self.assertContains(response, self.patch.name)

    def testMboxView(self):
        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.patch.content in \
                response.content.decode(self.patch_encoding))

    def testRawView(self):
        response = self.client.get('/patch/%d/raw/' % self.patch.id)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content.decode(self.patch_encoding),
                self.patch.content)

    def tearDown(self):
        self.patch.delete()
        defaults.patch_author_person.delete()
        defaults.project.delete()

