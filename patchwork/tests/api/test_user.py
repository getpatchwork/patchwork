# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.tests.api import utils
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

    @utils.store_samples('users-list-error-forbidden')
    def test_list_anonymous(self):
        """List users as anonymous user."""
        create_user()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('users-list')
    def test_list_authenticated(self):
        """List users as authenticated user."""
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(user, resp.data[0])

    @utils.store_samples('users-detail-error-forbidden')
    def test_detail_anonymous(self):
        """Show user as anonymous user."""
        user = create_user()

        resp = self.client.get(self.api_url(user.id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('users-detail')
    def test_detail_authenticated(self):
        """Show user as authenticated user."""
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(user.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data)

    @utils.store_samples('users-update-error-forbidden')
    def test_update_anonymous(self):
        """Update user as anonymous user."""
        user = create_user()

        resp = self.client.patch(self.api_url(user.id), {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_update_other_user(self):
        """Update user as another, non-maintainer user."""
        user_a = create_user()
        user_b = create_user()

        self.client.force_authenticate(user=user_a)
        resp = self.client.patch(self.api_url(user_b.id),
                                 {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_update_maintainer(self):
        """Update user as maintainer."""
        user = create_maintainer()
        user.is_superuser = True
        user.save()

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(user.id), {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data)

    @utils.store_samples('users-update')
    def test_update_self(self):
        """Update user as self."""
        user = create_user()

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
