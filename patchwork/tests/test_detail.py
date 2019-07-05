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

from django.test import TestCase

from patchwork.compat import reverse
from patchwork.tests.utils import create_comment
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_series


class CoverLetterViewTest(TestCase):

    def test_redirect(self):
        patch_id = create_patch().id

        requested_url = reverse('cover-detail', kwargs={'cover_id': patch_id})
        redirect_url = reverse('patch-detail', kwargs={'patch_id': patch_id})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)


class PatchViewTest(TestCase):

    def test_redirect(self):
        cover_id = create_cover().id

        requested_url = reverse('patch-detail', kwargs={'patch_id': cover_id})
        redirect_url = reverse('cover-detail', kwargs={'cover_id': cover_id})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_series_dropdown(self):
        patch = create_patch()
        series = [create_series() for x in range(5)]

        for series_ in series:
            series_.add_patch(patch, 1)

        response = self.client.get(
            reverse('patch-detail', kwargs={'patch_id': patch.id}))

        for series_ in series:
            self.assertContains(
                response,
                reverse('series-mbox', kwargs={'series_id': series_.id}))

    def test_escaping(self):
        # Warning: this test doesn't guarantee anything - it only tests some
        # fields
        unescaped_string = 'blah<b>TEST</b>blah'
        patch = create_patch()
        patch.diff = unescaped_string
        patch.commit_ref = unescaped_string
        patch.pull_url = unescaped_string
        patch.name = unescaped_string
        patch.msgid = unescaped_string
        patch.headers = unescaped_string
        patch.content = unescaped_string
        patch.save()
        requested_url = reverse('patch-detail', kwargs={'patch_id': patch.id})
        response = self.client.get(requested_url)
        self.assertNotIn('<b>TEST</b>'.encode('utf-8'), response.content)


class CommentRedirectTest(TestCase):

    def _test_redirect(self, submission, submission_url, submission_id):
        comment_id = create_comment(submission=submission).id

        requested_url = reverse('comment-redirect',
                                kwargs={'comment_id': comment_id})
        redirect_url = '%s#%d' % (
            reverse(submission_url, kwargs={submission_id: submission.id}),
            comment_id)

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_patch_redirect(self):
        patch = create_patch()
        self._test_redirect(patch, 'patch-detail', 'patch_id')

    def test_cover_redirect(self):
        cover = create_cover()
        self._test_redirect(cover, 'cover-detail', 'cover_id')
