# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestSeriesAPI(APITestCase):
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

    def test_list(self):
        """Validate we can list series."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        project_obj = create_project(linkname='myproject')
        person_obj = create_person(email='test@example.com')
        series_obj = create_series(project=project_obj, submitter=person_obj)
        create_cover(series=series_obj)
        create_patch(series=series_obj)

        # anonymous users
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        series_rsp = resp.data[0]
        self.assertSerialized(series_obj, series_rsp)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        series_rsp = resp.data[0]
        self.assertSerialized(series_obj, series_rsp)

        # test filtering by project
        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([series_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

        # test filtering by owner, both ID and email
        resp = self.client.get(self.api_url(), {'submitter': person_obj.id})
        self.assertEqual([series_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.com'})
        self.assertEqual([series_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.org'})
        self.assertEqual(0, len(resp.data))

    def test_list_old_version(self):
        """Validate that newer fields are dropped for older API versions."""
        create_series()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_detail(self):
        """Validate we can get a specific series."""
        series = create_series()
        create_cover(series=series)

        resp = self.client.get(self.api_url(series.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(series, resp.data)

    def test_detail_version_1_0(self):
        series = create_series()

        resp = self.client.get(self.api_url(series.id, version='1.0'))
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)

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
