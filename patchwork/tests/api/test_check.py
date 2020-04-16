# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.models import Check
from patchwork.tests.api import utils
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase as BaseAPITestCase
else:
    # stub out APITestCase
    from django.test import TestCase as BaseAPITestCase


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCheckAPI(utils.APITestCase):
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

    def _create_check(self, patch=None):
        values = {
            'patch': patch if patch else self.patch,
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

    def test_list_empty(self):
        """List checks when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('check-list')
    def test_list(self):
        """List checks."""
        check_obj = self._create_check()
        self._create_check(create_patch())  # second, unrelated patch

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(check_obj, resp.data[0])

    def test_list_filter_user(self):
        """Filter checks by user."""
        check_obj = self._create_check()

        # test filtering by owner, both ID and username
        resp = self.client.get(self.api_url(), {'user': self.user.id})
        self.assertEqual([check_obj.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {'user': self.user.username})
        self.assertEqual([check_obj.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {'user': 'otheruser'})
        self.assertEqual(0, len(resp.data))

    def test_list_invalid_patch(self):
        """Ensure we get a 404 for a non-existent patch."""
        resp = self.client.get(
            reverse('api-check-list', kwargs={'patch_id': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    @utils.store_samples('check-detail')
    def test_detail(self):
        """Show a check."""
        check = self._create_check()
        resp = self.client.get(self.api_url(check))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(check, resp.data)

    def _test_create(self, user):
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=user)
        return self.client.post(self.api_url(), check)

    @utils.store_samples('check-create-error-forbidden')
    def test_create_non_maintainer(self):
        """Create a check as a non-maintainer.

        Ensure creations can only be performed by maintainers.
        """
        user = create_user()

        resp = self._test_create(user=user)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('check-create')
    def test_create_maintainer(self):
        """Create a check as a maintainer.

        Ensure creations can only be performed by maintainers.
        """
        resp = self._test_create(user=self.user)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())
        self.assertSerialized(Check.objects.first(), resp.data)

    @utils.store_samples('check-create-error-bad-request')
    def test_create_invalid_state(self):
        """Create a check using invalid values.

        Ensure we handle invalid check states.
        """
        check = {
            'state': 'this-is-not-a-valid-state',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check, validate_request=False)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())

    @utils.store_samples('check-create-error-missing-state')
    def test_create_missing_state(self):
        """Create a check using invalid values.

        Ensure we handle the state being absent.
        """
        check = {
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check, validate_request=False)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())

    @utils.store_samples('check-create-error-not-found')
    def test_create_invalid_patch(self):
        """Ensure we handle non-existent patches."""
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            reverse('api-check-list', kwargs={'patch_id': '99999'}), check)
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

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


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCheckAPIMultipart(BaseAPITestCase):
    """Test a minimal subset of functionality where the data is passed as
    multipart form data rather than as a JSON blob.

    We focus on the POST path exclusively and only on state validation:
    everything else should be handled in the JSON tests.

    This is required due to the difference in handling JSON vs form-data in
    CheckSerializer's run_validation().
    """
    fixtures = ['default_tags']

    def setUp(self):
        super(TestCheckAPIMultipart, self).setUp()
        project = create_project()
        self.user = create_maintainer(project)
        self.patch = create_patch(project=project)

    def assertSerialized(self, check_obj, check_json):
        self.assertEqual(check_obj.id, check_json['id'])
        self.assertEqual(check_obj.get_state_display(), check_json['state'])
        self.assertEqual(check_obj.target_url, check_json['target_url'])
        self.assertEqual(check_obj.context, check_json['context'])
        self.assertEqual(check_obj.description, check_json['description'])
        self.assertEqual(check_obj.user.id, check_json['user']['id'])

    def _test_create(self, user, state='success'):
        check = {
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }
        if state is not None:
            check['state'] = state

        self.client.force_authenticate(user=user)
        return self.client.post(
            reverse('api-check-list', args=[self.patch.id]),
            check)

    def test_creates(self):
        """Create a set of checks.
        """
        resp = self._test_create(user=self.user)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())
        self.assertSerialized(Check.objects.last(), resp.data)

        resp = self._test_create(user=self.user, state='pending')
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(2, Check.objects.all().count())
        self.assertSerialized(Check.objects.last(), resp.data)

        # you can also use the numeric ID of the state, the API explorer does
        resp = self._test_create(user=self.user, state=2)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(3, Check.objects.all().count())
        # we check against the string version
        resp.data['state'] = 'warning'
        self.assertSerialized(Check.objects.last(), resp.data)
