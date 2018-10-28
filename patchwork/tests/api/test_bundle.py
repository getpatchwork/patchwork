# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.tests.api import utils
from patchwork.tests.utils import create_bundle
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestBundleAPI(APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-bundle-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-bundle-detail', kwargs=kwargs)

    def assertSerialized(self, bundle_obj, bundle_json):
        self.assertEqual(bundle_obj.id, bundle_json['id'])
        self.assertEqual(bundle_obj.name, bundle_json['name'])
        self.assertEqual(bundle_obj.public, bundle_json['public'])
        self.assertIn(bundle_obj.get_mbox_url(), bundle_json['mbox'])
        self.assertIn(bundle_obj.get_absolute_url(), bundle_json['web_url'])

        # nested fields

        self.assertEqual(bundle_obj.patches.count(),
                         len(bundle_json['patches']))
        self.assertEqual(bundle_obj.owner.id,
                         bundle_json['owner']['id'])
        self.assertEqual(bundle_obj.project.id,
                         bundle_json['project']['id'])

    def test_list_empty(self):
        """List bundles when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def _create_bundles(self):
        user = create_user(username='myuser')
        project = create_project(linkname='myproject')
        bundle_public = create_bundle(public=True, owner=user,
                                      project=project)
        bundle_private = create_bundle(public=False, owner=user,
                                       project=project)

        return user, project, bundle_public, bundle_private

    def test_list_anonymous(self):
        """List bundles as anonymous user."""
        user, project, bundle_public, _ = self._create_bundles()

        # anonymous users
        # should only see the public bundle
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        bundle_rsp = resp.data[0]
        self.assertSerialized(bundle_public, bundle_rsp)

    @utils.store_samples('bundle-list')
    def test_list_authenticated(self):
        """List bundles as an authenticated user."""
        user, project, bundle_public, bundle_private = self._create_bundles()

        # authenticated user
        # should see the public and private bundle
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))
        for bundle_rsp, bundle_obj in zip(
                resp.data, [bundle_public, bundle_private]):
            self.assertSerialized(bundle_obj, bundle_rsp)

    def test_list_filter_project(self):
        """Filter bundles by project."""
        user, project, bundle_public, bundle_private = self._create_bundles()

        # test filtering by project
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_owner(self):
        """Filter bundles by owner."""
        user, project, bundle_public, bundle_private = self._create_bundles()

        # test filtering by owner, both ID and username
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(), {'owner': user.id})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'owner': 'myuser'})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'owner': 'otheruser'})
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('bundle-list-1.0')
    def test_list_version_1_0(self):
        """List bundles using API v1.0.

        Validate that newer fields are dropped for older API versions.
        """
        user, _, _, _ = self._create_bundles()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_detail_anonymous_public(self):
        """Show public bundle as anonymous user.

        Validate we can get a public bundle.
        """
        user, _, bundle, _ = self._create_bundles()

        resp = self.client.get(self.api_url(bundle.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(bundle, resp.data)

    @utils.store_samples('bundle-detail-error-not-found')
    def test_detail_anonymous_private(self):
        """Show private bundle as anonymous user.

        Validate we cannot get a private bundle if we're not the owner.
        """
        user, _, _, bundle = self._create_bundles()

        resp = self.client.get(self.api_url(bundle.id))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    @utils.store_samples('bundle-detail')
    def test_detail_authenticated(self):
        """Show private bundle as authenticated user.

        Validate we can get a private bundle if we're the owner.
        """
        user, _, _, bundle = self._create_bundles()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(bundle.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(bundle, resp.data)

    @utils.store_samples('bundle-detail-1.0')
    def test_detail_version_1_0(self):
        """Show bundle using API v1.0."""
        user, _, bundle, _ = self._create_bundles()

        resp = self.client.get(self.api_url(bundle.id, version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)

    def test_create_update_delete(self):
        """Ensure creates, updates and deletes aren't allowed"""
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.patch(self.api_url(user.id), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(1))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
