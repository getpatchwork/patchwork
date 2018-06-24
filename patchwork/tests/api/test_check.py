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

from patchwork.models import Check
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_patch
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
class TestCheckAPI(APITestCase):
    fixtures = ['default_tags']

    def api_url(self, item=None):
        if item is None:
            return reverse('api-check-list', args=[self.patch.id])
        return reverse('api-check-detail', kwargs={
            'patch_id': self.patch.id, 'check_id': item.id})

    def setUp(self):
        super(TestCheckAPI, self).setUp()
        project = create_project()
        self.user = create_maintainer(project)
        self.patch = create_patch(project=project)

    def _create_check(self):
        values = {
            'patch': self.patch,
            'user': self.user,
        }
        return create_check(**values)

    def assertSerialized(self, check_obj, check_json):
        self.assertEqual(check_obj.id, check_json['id'])
        self.assertEqual(check_obj.get_state_display(), check_json['state'])
        self.assertEqual(check_obj.target_url, check_json['target_url'])
        self.assertEqual(check_obj.context, check_json['context'])
        self.assertEqual(check_obj.description, check_json['description'])
        self.assertEqual(check_obj.user.id, check_json['user']['id'])

    def test_list(self):
        """Validate we can list checks on a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        check_obj = self._create_check()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(check_obj, resp.data[0])

        # test filtering by owner, both ID and username
        resp = self.client.get(self.api_url(), {'user': self.user.id})
        self.assertEqual([check_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'user': self.user.username})
        self.assertEqual([check_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'user': 'otheruser'})
        self.assertEqual(0, len(resp.data))

    def test_detail(self):
        """Validate we can get a specific check."""
        check = self._create_check()
        resp = self.client.get(self.api_url(check))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(check, resp.data)

    def test_create(self):
        """Ensure creations can be performed by user of patch."""
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())
        self.assertSerialized(Check.objects.first(), resp.data)

        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create_invalid(self):
        """Ensure we handle invalid check states."""
        check = {
            'state': 'this-is-not-a-valid-state',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())

    def test_update_delete(self):
        """Ensure updates and deletes aren't allowed"""
        check = self._create_check()
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        resp = self.client.patch(self.api_url(check), {'target_url': 'fail'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(check))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
