# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.tests.api import utils
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestSeriesAPI(utils.APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-series-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-series-detail', kwargs=kwargs)

    def assertSerialized(self, series_obj, series_json):
        self.assertEqual(series_obj.id, series_json['id'])
        self.assertEqual(series_obj.name, series_json['name'])
        self.assertEqual(series_obj.version, series_json['version'])
        self.assertEqual(series_obj.total, series_json['total'])
        self.assertEqual(series_obj.received_total,
                         series_json['received_total'])
        self.assertIn(series_obj.get_mbox_url(), series_json['mbox'])
        self.assertIn(series_obj.get_absolute_url(), series_json['web_url'])

        # nested fields

        self.assertEqual(series_obj.project.id,
                         series_json['project']['id'])
        self.assertEqual(series_obj.submitter.id,
                         series_json['submitter']['id'])
        self.assertEqual(series_obj.cover_letter.id,
                         series_json['cover_letter']['id'])
        self.assertEqual(series_obj.patches.count(),
                         len(series_json['patches']))

    def test_list_empty(self):
        """List series when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def _create_series(self):
        project_obj = create_project(linkname='myproject')
        person_obj = create_person(email='test@example.com')
        series_obj = create_series(project=project_obj, submitter=person_obj)
        create_cover(series=series_obj)
        create_patch(series=series_obj)

        return series_obj

    def test_list_anonymous(self):
        """List patches as anonymous user."""
        series = self._create_series()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        series_rsp = resp.data[0]
        self.assertSerialized(series, series_rsp)

    @utils.store_samples('series-list')
    def test_list_authenticated(self):
        """List series as an authenticated user."""
        series = self._create_series()
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        series_rsp = resp.data[0]
        self.assertSerialized(series, series_rsp)

    def test_list_filter_project(self):
        """Filter series by project."""
        series = self._create_series()

        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([series.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_owner(self):
        """Filter series by owner."""
        series = self._create_series()
        submitter = series.submitter

        resp = self.client.get(self.api_url(), {'submitter': submitter.id})
        self.assertEqual([series.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.com'})
        self.assertEqual([series.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.org'})
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('series-list-1-0')
    def test_list_version_1_0(self):
        """List patches using API v1.0.

        Validate that newer fields are dropped for older API versions.
        """
        self._create_series()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0]['cover_letter'])
        self.assertNotIn('mbox', resp.data[0]['cover_letter'])
        self.assertNotIn('web_url', resp.data[0]['patches'][0])

    def test_list_bug_335(self):
        """Ensure we retrieve the embedded cover letter project in O(1)."""
        project_obj = create_project(linkname='myproject')
        person_obj = create_person(email='test@example.com')
        for i in range(10):
            series_obj = create_series(
                project=project_obj, submitter=person_obj,
            )
            create_cover(series=series_obj)
            create_patch(series=series_obj)

        with self.assertNumQueries(6):
            self.client.get(self.api_url())

    @utils.store_samples('series-detail')
    def test_detail(self):
        """Show series."""
        series = self._create_series()

        resp = self.client.get(self.api_url(series.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(series, resp.data)

    @utils.store_samples('series-detail-1-0')
    def test_detail_version_1_0(self):
        """Show series using API v1.0."""
        series = self._create_series()

        resp = self.client.get(self.api_url(series.id, version='1.0'))
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)
        self.assertNotIn('web_url', resp.data['cover_letter'])
        self.assertNotIn('mbox', resp.data['cover_letter'])
        self.assertNotIn('web_url', resp.data['patches'][0])

    def test_detail_non_existent(self):
        """Ensure we get a 404 for a non-existent series."""
        resp = self.client.get(self.api_url('999999'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_detail_invalid(self):
        """Ensure we get a 404 for an invalid series ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url('foo'))

    def test_create_update_delete(self):
        """Ensure creates, updates and deletes aren't allowed"""
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'name': 'Test'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        series = create_series()

        resp = self.client.patch(self.api_url(series.id), {'name': 'Test'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(series.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
