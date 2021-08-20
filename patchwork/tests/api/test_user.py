# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.tests.api import utils
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestUserAPI(utils.APITestCase):

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-user-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-user-detail', kwargs=kwargs)

    def assertSerialized(self, user_obj, user_json, has_settings=False):
        user_obj.refresh_from_db()
        user_obj.profile.refresh_from_db()

        self.assertEqual(user_obj.id, user_json['id'])
        self.assertEqual(user_obj.username, user_json['username'])
        self.assertNotIn('password', user_json)
        self.assertNotIn('is_superuser', user_json)

        if has_settings:
            self.assertIn('settings', user_json)
            self.assertEqual(user_json['settings']['send_email'],
                             user_obj.profile.send_email)
            self.assertEqual(user_json['settings']['items_per_page'],
                             user_obj.profile.items_per_page)
            self.assertEqual(user_json['settings']['show_ids'],
                             user_obj.profile.show_ids)
        else:
            self.assertNotIn('settings', user_json)

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
        """Show user as a user other than self."""
        user_a = create_user()
        user_b = create_user()

        self.client.force_authenticate(user=user_a)
        resp = self.client.get(self.api_url(user_b.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user_b, resp.data, has_settings=False)

    @utils.store_samples('users-detail-self')
    def test_detail_self(self):
        """Show user as self."""
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(user.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data, has_settings=True)

    def test_detail_non_existent(self):
        """Ensure we get a 404 for a non-existent user."""
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url('999999'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_detail_invalid(self):
        """Ensure we get a 404 for an invalid user ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url('foo'))

    @utils.store_samples('users-update-error-forbidden')
    def test_update_anonymous(self):
        """Update user as anonymous user."""
        user = create_user()

        resp = self.client.patch(self.api_url(user.id), {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('users-update')
    def test_update_other_user(self):
        """Update user as a user other than self."""
        user_a = create_user()
        user_b = create_user()

        self.client.force_authenticate(user=user_a)
        resp = self.client.patch(self.api_url(user_b.id),
                                 {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('users-update-self')
    def test_update_self(self):
        """Update user as self."""
        user = create_user()
        self.assertFalse(user.profile.send_email)

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(user.id), {
            'first_name': 'Tan', 'settings': {'send_email': True}})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data, has_settings=True)
        self.assertEqual('Tan', user.first_name)
        self.assertTrue(user.profile.send_email)

    def test_update_self_version_1_1(self):
        """Update user as self using the old API.

        Ensure the profile changes are ignored.
        """
        user = create_user()
        self.assertFalse(user.profile.send_email)

        self.client.force_authenticate(user=user)
        resp = self.client.patch(
            self.api_url(user.id, version='1.1'),
            {'first_name': 'Tan', 'settings': {'send_email': True}},
            validate_request=False)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(user, resp.data, has_settings=False)
        self.assertEqual('Tan', user.first_name)
        self.assertFalse(user.profile.send_email)

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
