# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
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

from patchwork.compat import NoReverseMatch
from patchwork.compat import reverse
from patchwork.tests.utils import create_comment
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import SAMPLE_CONTENT

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCoverComments(APITestCase):
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

    def test_list(self):
        cover_obj = create_cover()
        resp = self.client.get(self.api_url(cover_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        comment_obj = create_comment(submission=cover_obj)
        resp = self.client.get(self.api_url(cover_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment_obj, resp.data[0])

        create_comment(submission=cover_obj)
        resp = self.client.get(self.api_url(cover_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))

        # check we can't access comments using the old version of the API
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(cover_obj, version='1.0'))

    def test_list_invalid_cover(self):
        """Ensure we get a 404 for a non-existent cover letter."""
        resp = self.client.get(
            reverse('api-cover-comment-list', kwargs={'pk': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchComments(APITestCase):
    @staticmethod
    def api_url(patch, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version
        kwargs['pk'] = patch.id

        return reverse('api-patch-comment-list', kwargs=kwargs)

    def assertSerialized(self, comment_obj, comment_json):
        self.assertEqual(comment_obj.id, comment_json['id'])
        self.assertEqual(comment_obj.submitter.id,
                         comment_json['submitter']['id'])
        self.assertIn(SAMPLE_CONTENT, comment_json['content'])

    def test_list(self):
        patch_obj = create_patch()
        resp = self.client.get(self.api_url(patch_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        comment_obj = create_comment(submission=patch_obj)
        resp = self.client.get(self.api_url(patch_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment_obj, resp.data[0])

        create_comment(submission=patch_obj)
        resp = self.client.get(self.api_url(patch_obj))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))

        # check we can't access comments using the old version of the API
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(patch_obj, version='1.0'))

    def test_list_invalid_patch(self):
        """Ensure we get a 404 for a non-existent patch."""
        resp = self.client.get(
            reverse('api-patch-comment-list', kwargs={'pk': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)
