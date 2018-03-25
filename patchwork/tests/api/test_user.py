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

from patchwork.compat import reverse
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestUserAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-user-list')
        return reverse('api-user-detail', args=[item])

    def assertSerialized(self, user_obj, user_json):
        self.assertEqual(user_obj.id, user_json['id'])
        self.assertEqual(user_obj.username, user_json['username'])
        self.assertNotIn('password', user_json)
        self.assertNotIn('is_superuser', user_json)

    def test_list(self):
        """This API requires authenticated users."""
        # anonymous users
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(user, resp.data[0])

    def test_update(self):
        """Ensure updates are allowed."""
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.patch(self.api_url(user.id), {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data)

    def test_create_delete(self):
        """Ensure creations and deletions and not allowed."""
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(user.id), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
