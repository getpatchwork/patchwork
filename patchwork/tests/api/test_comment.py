# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.tests.api import utils
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import SAMPLE_CONTENT

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCoverComments(utils.APITestCase):
    @staticmethod
    def api_url(cover, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version
        kwargs['pk'] = cover.id

        return reverse('api-cover-comment-list', kwargs=kwargs)

    def assertSerialized(self, comment_obj, comment_json):
        self.assertEqual(comment_obj.id, comment_json['id'])
        self.assertEqual(comment_obj.submitter.id,
                         comment_json['submitter']['id'])
        self.assertIn(SAMPLE_CONTENT, comment_json['content'])

    def test_list_empty(self):
        """List cover letter comments when none are present."""
        cover = create_cover()
        resp = self.client.get(self.api_url(cover))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('cover-comment-list')
    def test_list(self):
        """List cover letter comments."""
        cover = create_cover()
        comment = create_cover_comment(cover=cover)

        resp = self.client.get(self.api_url(cover))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertIn('list_archive_url', resp.data[0])

    def test_list_version_1_1(self):
        """List cover letter comments using API v1.1."""
        cover = create_cover()
        comment = create_cover_comment(cover=cover)

        resp = self.client.get(self.api_url(cover, version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertNotIn('list_archive_url', resp.data[0])

    def test_list_version_1_0(self):
        """List cover letter comments using API v1.0."""
        cover = create_cover()
        create_cover_comment(cover=cover)

        # check we can't access comments using the old version of the API
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(cover, version='1.0'))

    def test_list_invalid_cover(self):
        """Ensure we get a 404 for a non-existent cover letter."""
        resp = self.client.get(
            reverse('api-cover-comment-list', kwargs={'pk': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchComments(utils.APITestCase):
    @staticmethod
    def api_url(patch, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version
        kwargs['patch_id'] = patch.id

        return reverse('api-patch-comment-list', kwargs=kwargs)

    def assertSerialized(self, comment_obj, comment_json):
        self.assertEqual(comment_obj.id, comment_json['id'])
        self.assertEqual(comment_obj.submitter.id,
                         comment_json['submitter']['id'])
        self.assertIn(SAMPLE_CONTENT, comment_json['content'])

    def test_list_empty(self):
        """List patch comments when none are present."""
        patch = create_patch()
        resp = self.client.get(self.api_url(patch))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('patch-comment-list')
    def test_list(self):
        """List patch comments."""
        patch = create_patch()
        comment = create_patch_comment(patch=patch)

        resp = self.client.get(self.api_url(patch))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertIn('list_archive_url', resp.data[0])

    def test_list_version_1_1(self):
        """List patch comments using API v1.1."""
        patch = create_patch()
        comment = create_patch_comment(patch=patch)

        resp = self.client.get(self.api_url(patch, version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertNotIn('list_archive_url', resp.data[0])

    def test_list_version_1_0(self):
        """List patch comments using API v1.0."""
        patch = create_patch()
        create_patch_comment(patch=patch)

        # check we can't access comments using the old version of the API
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(patch, version='1.0'))

    def test_list_invalid_patch(self):
        """Ensure we get a 404 for a non-existent patch."""
        resp = self.client.get(
            reverse('api-patch-comment-list', kwargs={'patch_id': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
