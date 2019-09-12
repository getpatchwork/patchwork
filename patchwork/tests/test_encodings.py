# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import read_patch


class UTF8PatchViewTest(TestCase):

    def setUp(self):
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(diff=patch_content)

    def test_patch_view(self):
        response = self.client.get(reverse(
            'patch-detail', args=[self.patch.project.linkname,
                                  self.patch.url_msgid]))
        self.assertContains(response, self.patch.name)

    def test_mbox_view(self):
        response = self.client.get(
            reverse('patch-mbox', args=[self.patch.project.linkname,
                                        self.patch.url_msgid]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.patch.diff in response.content.decode('utf-8'))

    def test_raw_view(self):
        response = self.client.get(reverse('patch-raw',
                                           args=[self.patch.project.linkname,
                                                 self.patch.url_msgid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), self.patch.diff)


class UTF8HeaderPatchViewTest(UTF8PatchViewTest):

    def setUp(self):
        author = create_person(name=u'P\xe4tch Author')
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(submitter=author, diff=patch_content)
