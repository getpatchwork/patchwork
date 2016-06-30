# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
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

from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.tests.utils import create_covers
from patchwork.tests.utils import create_patches


class CoverLetterViewTest(TestCase):

    def test_redirect(self):
        patches = create_patches()
        patch_id = patches[0].id

        requested_url = reverse('cover-detail', kwargs={'cover_id': patch_id})
        redirect_url = reverse('patch-detail', kwargs={'patch_id': patch_id})

        response = self.client.post(requested_url)
        self.assertRedirects(response, redirect_url)


class PatchViewTest(TestCase):

    def test_redirect(self):
        covers = create_covers()
        cover_id = covers[0].id

        requested_url = reverse('patch-detail', kwargs={'patch_id': cover_id})
        redirect_url = reverse('cover-detail', kwargs={'cover_id': cover_id})

        response = self.client.post(requested_url)
        self.assertRedirects(response, redirect_url)
