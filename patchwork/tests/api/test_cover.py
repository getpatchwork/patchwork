# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser
import unittest

from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.tests.api import utils
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_covers
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCoverAPI(utils.APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-cover-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-cover-detail', kwargs=kwargs)

    def assertSerialized(self, cover_obj, cover_json):
        self.assertEqual(cover_obj.id, cover_json['id'])
        self.assertEqual(cover_obj.name, cover_json['name'])
        self.assertIn(cover_obj.get_mbox_url(), cover_json['mbox'])
        self.assertIn(cover_obj.get_absolute_url(), cover_json['web_url'])
        self.assertIn('comments', cover_json)

        # nested fields

        self.assertEqual(cover_obj.submitter.id,
                         cover_json['submitter']['id'])

        if hasattr(cover_obj, 'series'):
            self.assertEqual(1, len(cover_json['series']))
            self.assertEqual(cover_obj.series.id,
                             cover_json['series'][0]['id'])
        else:
            self.assertEqual([], cover_json['series'])

    def test_list_empty(self):
        """List cover letters when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def test_list_anonymous(self):
        """List cover letter as anonymous user."""
        # we specifically set series to None to test code that handles legacy
        # cover letters created before series existed
        cover = create_cover(series=None)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(cover, resp.data[0])

    @utils.store_samples('cover-list')
    def test_list_authenticated(self):
        """List cover letters as an authenticated user."""
        cover = create_cover()
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(cover, resp.data[0])

    def test_list_filter_project(self):
        """Filter cover letters by project."""
        cover = create_cover()
        project = cover.project

        resp = self.client.get(self.api_url(), {'project': project.linkname})
        self.assertEqual([cover.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_submitter(self):
        """Filter cover letter by submitter."""
        cover = create_cover()
        submitter = cover.submitter

        # test filtering by submitter, both ID and email
        resp = self.client.get(self.api_url(), {'submitter': submitter.id})
        self.assertEqual([cover.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': submitter.email})
        self.assertEqual([cover.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.org'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_msgid(self):
        """Filter covers by msgid."""
        cover = create_cover()

        resp = self.client.get(self.api_url(), {'msgid': cover.url_msgid})
        self.assertEqual([cover.id], [x['id'] for x in resp.data])

        # empty response if nothing matches
        resp = self.client.get(self.api_url(), {
            'msgid': 'fishfish@fish.fish'})
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('cover-list-1-0')
    def test_list_version_1_0(self):
        create_cover()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('mbox', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_list_bug_335(self):
        """Ensure we retrieve the embedded series project once."""
        series = create_series()
        create_covers(5, series=series)

        with self.assertNumQueries(3):
            self.client.get(self.api_url())

    @utils.store_samples('cover-detail')
    def test_detail(self):
        """Validate we can get a specific cover letter."""
        cover_obj = create_cover(
            headers='Received: from somewhere\nReceived: from another place'
        )

        resp = self.client.get(self.api_url(cover_obj.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(cover_obj, resp.data)

        # Make sure we don't regress and all headers with the same key are
        # included in the response
        parsed_headers = email.parser.Parser().parsestr(cover_obj.headers,
                                                        True)
        for key, value in parsed_headers.items():
            self.assertIn(value, resp.data['headers'][key])

    @utils.store_samples('cover-detail-1-0')
    def test_detail_version_1_0(self):
        cover = create_cover()

        resp = self.client.get(self.api_url(cover.id, version='1.0'))
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)
        self.assertNotIn('comments', resp.data)

    def test_detail_non_existent(self):
        """Ensure we get a 404 for a non-existent cover."""
        resp = self.client.get(self.api_url('999999'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_detail_invalid(self):
        """Ensure we get a 404 for an invalid cover ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url('foo'))

    def test_create_update_delete(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'name': 'test cover'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.patch(self.api_url(), {'name': 'test cover'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url())
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
