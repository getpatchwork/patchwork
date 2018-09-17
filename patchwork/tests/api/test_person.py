# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPersonAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-person-list')
        return reverse('api-person-detail', args=[item])

    def assertSerialized(self, person_obj, person_json, has_user=False):
        self.assertEqual(person_obj.id, person_json['id'])
        if not has_user:
            self.assertEqual(person_obj.name, person_json['name'])
            self.assertEqual(person_obj.email, person_json['email'])
        else:
            self.assertEqual(person_obj.user.username, person_json['name'])
            self.assertEqual(person_obj.user.email, person_json['email'])
            # nested fields
            self.assertEqual(person_obj.user.id,
                             person_json['user']['id'])

    def test_list(self):
        """This API requires authenticated users."""
        person = create_person()

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user(link_person=False)
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(person, resp.data[0])

    def test_detail(self):
        person = create_person()

        # anonymous user
        resp = self.client.get(self.api_url(person.id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated, unlinked user
        user = create_user(link_person=False)
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url(person.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(person, resp.data, has_user=False)

        # authenticated, linked user
        user = create_user(link_person=True)
        person = user.person_set.all().first()
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url(person.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(person, resp.data, has_user=True)

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

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
