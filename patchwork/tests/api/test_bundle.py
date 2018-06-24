# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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
from django.urls import reverse

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

    def test_list(self):
        """Validate we can list bundles."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        user = create_user(username='myuser')
        project = create_project(linkname='myproject')
        bundle_public = create_bundle(public=True, owner=user,
                                      project=project)
        bundle_private = create_bundle(public=False, owner=user,
                                       project=project)

        # anonymous users
        # should only see the public bundle
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        bundle_rsp = resp.data[0]
        self.assertSerialized(bundle_public, bundle_rsp)

        # authenticated user
        # should see the public and private bundle
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))
        for bundle_rsp, bundle_obj in zip(
                resp.data, [bundle_public, bundle_private]):
            self.assertSerialized(bundle_obj, bundle_rsp)

        # test filtering by project
        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

        # test filtering by owner, both ID and username
        resp = self.client.get(self.api_url(), {'owner': user.id})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'owner': 'myuser'})
        self.assertEqual([bundle_public.id, bundle_private.id],
                         [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'owner': 'otheruser'})
        self.assertEqual(0, len(resp.data))

    def test_list_version_1_0(self):
        """Validate that newer fields are dropped for older API versions."""
        create_bundle(public=True)

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_detail(self):
        """Validate we can get a specific bundle."""
        bundle = create_bundle(public=True)

        resp = self.client.get(self.api_url(bundle.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(bundle, resp.data)

    def test_detail_version_1_0(self):
        bundle = create_bundle(public=True)

        resp = self.client.get(self.api_url(bundle.id, version='1.0'))
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
