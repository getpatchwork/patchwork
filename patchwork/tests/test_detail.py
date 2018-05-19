# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_comment
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_patch


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
