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
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import read_patch


class UTF8PatchViewTest(TestCase):

    fixtures = ['default_states']

    def setUp(self):
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(diff=patch_content)

    def test_patch_view(self):
        response = self.client.get(reverse(
            'patch-detail', args=[self.patch.id]))
        self.assertContains(response, self.patch.name)

    def test_mbox_view(self):
        response = self.client.get(reverse('patch-mbox', args=[self.patch.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.patch.diff in response.content.decode('utf-8'))

    def test_raw_view(self):
        response = self.client.get(reverse('patch-raw', args=[self.patch.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), self.patch.diff)


class UTF8HeaderPatchViewTest(UTF8PatchViewTest):

    fixtures = ['default_states']

    def setUp(self):
        author = create_person(name=u'P\xe4tch Author')
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(submitter=author, diff=patch_content)
