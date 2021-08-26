# Patchwork - automated patch tracking system
# Copyright (C) 2018 Red Hat
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.models import PatchComment
from patchwork.models import CoverComment
from patchwork.tests.api import utils
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_user
from patchwork.tests.utils import SAMPLE_CONTENT

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCoverComments(utils.APITestCase):

    @staticmethod
    def api_url(cover, version=None, item=None):
        kwargs = {'cover_id': cover.id}
        if version:
            kwargs['version'] = version
        if item is None:
            return reverse('api-cover-comment-list', kwargs=kwargs)
        kwargs['comment_id'] = item.id
        return reverse('api-cover-comment-detail', kwargs=kwargs)

    def setUp(self):
        super(TestCoverComments, self).setUp()
        self.project = create_project()
        self.user = create_maintainer(self.project)
        self.cover = create_cover(project=self.project)

    def assertSerialized(self, comment_obj, comment_json):
        self.assertEqual(comment_obj.id, comment_json['id'])
        self.assertEqual(comment_obj.submitter.id,
                         comment_json['submitter']['id'])
        self.assertEqual(comment_obj.addressed, comment_json['addressed'])
        self.assertIn(SAMPLE_CONTENT, comment_json['content'])

    def test_list_empty(self):
        """List cover letter comments when none are present."""
        cover = create_cover()
        resp = self.client.get(self.api_url(cover))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('cover-comment-list')
    def test_list(self):
        """List cover letter comments."""
        comment = create_cover_comment(cover=self.cover)

        resp = self.client.get(self.api_url(self.cover))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertIn('list_archive_url', resp.data[0])
        self.assertIn('addressed', resp.data[0])

    def test_list_version_1_2(self):
        """List cover letter comments using API v1.2."""
        create_cover_comment(cover=self.cover)

        resp = self.client.get(self.api_url(self.cover, version='1.2'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('list_archive_url', resp.data[0])
        self.assertNotIn('addressed', resp.data[0])

    def test_list_version_1_1(self):
        """List cover letter comments using API v1.1."""
        create_cover_comment(cover=self.cover)

        resp = self.client.get(self.api_url(self.cover, version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertNotIn('list_archive_url', resp.data[0])
        self.assertNotIn('addressed', resp.data[0])

    def test_list_version_1_0(self):
        """List cover letter comments using API v1.0.

        Ensure we can't access cover comments using the old version of the API.
        """
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(self.cover, version='1.0'))

    def test_list_non_existent_cover(self):
        """Ensure we get a 404 for a non-existent cover letter."""
        resp = self.client.get(
            reverse('api-cover-comment-list', kwargs={'cover_id': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_list_invalid_cover(self):
        """Ensure we get a 404 for an invalid cover letter ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(
                reverse('api-cover-comment-list', kwargs={'pk': 'foo'}),
            )

    @utils.store_samples('cover-comment-detail')
    def test_detail(self):
        """Show a cover letter comment."""
        comment = create_cover_comment(cover=self.cover)

        resp = self.client.get(self.api_url(self.cover, item=comment))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(comment, resp.data)

    def test_detail_version_1_2(self):
        """Show a cover letter comment using API v1.2."""
        comment = create_cover_comment(cover=self.cover)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.cover, version='1.2', item=comment))

    def test_detail_version_1_1(self):
        """Show a cover letter comment using API v1.1."""
        comment = create_cover_comment(cover=self.cover)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.cover, version='1.1', item=comment))

    def test_detail_version_1_0(self):
        """Show a cover letter comment using API v1.0."""
        comment = create_cover_comment(cover=self.cover)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.cover, version='1.0', item=comment))

    @utils.store_samples('cover-comment-detail-error-not-found')
    def test_detail_invalid_cover(self):
        """Ensure we handle non-existent cover letters."""
        comment = create_cover_comment()
        resp = self.client.get(
            reverse('api-cover-comment-detail', kwargs={
                'cover_id': '99999',
                'comment_id': comment.id}
            ),
        )
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def _test_update(self, person, **kwargs):
        submitter = kwargs.get('submitter', person)
        cover = kwargs.get('cover', self.cover)
        comment = create_cover_comment(submitter=submitter, cover=cover)

        if kwargs.get('authenticate', True):
            self.client.force_authenticate(user=person.user)
        return self.client.patch(
            self.api_url(cover, item=comment),
            {'addressed': kwargs.get('addressed', True)},
            validate_request=kwargs.get('validate_request', True)
        )

    @utils.store_samples('cover-comment-detail-update-authorized')
    def test_update_authorized(self):
        """Update an existing cover letter comment as an authorized user.

        To be authorized users must meet at least one of the following:
        - project maintainer, cover letter submitter, or cover letter
          comment submitter

        Ensure updates can only be performed by authorized users.
        """
        # Update as maintainer
        person = create_person(user=self.user)
        resp = self._test_update(person=person)
        self.assertEqual(1, CoverComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

        # Update as cover letter submitter
        person = create_person(name='cover-submitter', user=create_user())
        cover = create_cover(submitter=person)
        resp = self._test_update(person=person, cover=cover)
        self.assertEqual(2, CoverComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

        # Update as cover letter comment submitter
        person = create_person(name='comment-submitter', user=create_user())
        cover = create_cover()
        resp = self._test_update(person=person, cover=cover, submitter=person)
        self.assertEqual(3, CoverComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

    @utils.store_samples('cover-comment-detail-update-not-authorized')
    def test_update_not_authorized(self):
        """Update an existing cover letter comment when not signed in and
           not authorized.

        To be authorized users must meet at least one of the following:
        - project maintainer, cover letter submitter, or cover letter
          comment submitter

        Ensure updates can only be performed by authorized users.
        """
        person = create_person(user=self.user)
        resp = self._test_update(person=person, authenticate=False)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        person = create_person()  # normal user without edit permissions
        resp = self._test_update(person=person)  # signed-in
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('cover-comment-detail-update-error-bad-request')
    def test_update_invalid_addressed(self):
        """Update an existing cover letter comment using invalid values.

        Ensure we handle invalid cover letter comment addressed values.
        """
        person = create_person(name='cover-submitter', user=create_user())
        cover = create_cover(submitter=person)
        resp = self._test_update(person=person,
                                 cover=cover,
                                 addressed='not-valid',
                                 validate_request=False)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertFalse(
            getattr(CoverComment.objects.all().first(), 'addressed')
        )

    def test_create_delete(self):
        """Ensure creates and deletes aren't allowed"""
        comment = create_cover_comment(cover=self.cover)
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        resp = self.client.post(self.api_url(self.cover, item=comment))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(self.cover, item=comment))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchComments(utils.APITestCase):
    @staticmethod
    def api_url(patch, version=None, item=None):
        kwargs = {'patch_id': patch.id}
        if version:
            kwargs['version'] = version
        if item is None:
            return reverse('api-patch-comment-list', kwargs=kwargs)
        kwargs['comment_id'] = item.id
        return reverse('api-patch-comment-detail', kwargs=kwargs)

    def setUp(self):
        super(TestPatchComments, self).setUp()
        self.project = create_project()
        self.user = create_maintainer(self.project)
        self.patch = create_patch(project=self.project)

    def assertSerialized(self, comment_obj, comment_json):
        self.assertEqual(comment_obj.id, comment_json['id'])
        self.assertEqual(comment_obj.submitter.id,
                         comment_json['submitter']['id'])
        self.assertEqual(comment_obj.addressed, comment_json['addressed'])
        self.assertIn(SAMPLE_CONTENT, comment_json['content'])

    def test_list_empty(self):
        """List patch comments when none are present."""
        resp = self.client.get(self.api_url(self.patch))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('patch-comment-list')
    def test_list(self):
        """List patch comments."""
        comment = create_patch_comment(patch=self.patch)

        resp = self.client.get(self.api_url(self.patch))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(comment, resp.data[0])
        self.assertIn('list_archive_url', resp.data[0])
        self.assertIn('addressed', resp.data[0])

    def test_list_version_1_2(self):
        """List patch comments using API v1.2."""
        create_patch_comment(patch=self.patch)

        resp = self.client.get(self.api_url(self.patch, version='1.2'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('list_archive_url', resp.data[0])
        self.assertNotIn('addressed', resp.data[0])

    def test_list_version_1_1(self):
        """List patch comments using API v1.1."""
        create_patch_comment(patch=self.patch)

        resp = self.client.get(self.api_url(self.patch, version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertNotIn('list_archive_url', resp.data[0])
        self.assertNotIn('addressed', resp.data[0])

    def test_list_version_1_0(self):
        """List patch comments using API v1.0.

        Ensure we can't access comments using the old version of the API.
        """
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url(self.patch, version='1.0'))

    def test_list_non_existent_patch(self):
        """Ensure we get a 404 for a non-existent patch."""
        resp = self.client.get(
            reverse('api-patch-comment-list', kwargs={'patch_id': '99999'}))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_list_invalid_patch(self):
        """Ensure we get a 404 for an invalid patch ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(
                reverse('api-patch-comment-list', kwargs={'patch_id': 'foo'}),
            )

    @utils.store_samples('patch-comment-detail')
    def test_detail(self):
        """Show a patch comment."""
        comment = create_patch_comment(patch=self.patch)

        resp = self.client.get(self.api_url(self.patch, item=comment))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(comment, resp.data)

    def test_detail_version_1_2(self):
        """Show a patch comment using API v1.2."""
        comment = create_patch_comment(patch=self.patch)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.patch, version='1.2', item=comment))

    def test_detail_version_1_1(self):
        """Show a patch comment using API v1.1."""
        comment = create_patch_comment(patch=self.patch)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.patch, version='1.1', item=comment))

    def test_detail_version_1_0(self):
        """Show a patch comment using API v1.0."""
        comment = create_patch_comment(patch=self.patch)

        with self.assertRaises(NoReverseMatch):
            self.client.get(
                self.api_url(self.patch, version='1.0', item=comment))

    @utils.store_samples('patch-comment-detail-error-not-found')
    def test_detail_invalid_patch(self):
        """Ensure we handle non-existent patches."""
        comment = create_patch_comment()
        resp = self.client.get(
            reverse('api-patch-comment-detail', kwargs={
                'patch_id': '99999',
                'comment_id': comment.id}
            ),
        )
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def _test_update(self, person, **kwargs):
        submitter = kwargs.get('submitter', person)
        patch = kwargs.get('patch', self.patch)
        comment = create_patch_comment(submitter=submitter, patch=patch)

        if kwargs.get('authenticate', True):
            self.client.force_authenticate(user=person.user)
        return self.client.patch(
            self.api_url(patch, item=comment),
            {'addressed': kwargs.get('addressed', True)},
            validate_request=kwargs.get('validate_request', True)
        )

    @utils.store_samples('patch-comment-detail-update-authorized')
    def test_update_authorized(self):
        """Update an existing patch comment as an authorized user.

        To be authorized users must meet at least one of the following:
        - project maintainer, patch submitter, patch delegate, or
          patch comment submitter

        Ensure updates can only be performed by authorized users.
        """
        # Update as maintainer
        person = create_person(user=self.user)
        resp = self._test_update(person=person)
        self.assertEqual(1, PatchComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

        # Update as patch submitter
        person = create_person(name='patch-submitter', user=create_user())
        patch = create_patch(submitter=person)
        resp = self._test_update(person=person, patch=patch)
        self.assertEqual(2, PatchComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

        # Update as patch delegate
        person = create_person(name='patch-delegate', user=create_user())
        patch = create_patch(delegate=person.user)
        resp = self._test_update(person=person, patch=patch)
        self.assertEqual(3, PatchComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

        # Update as patch comment submitter
        person = create_person(name='comment-submitter', user=create_user())
        patch = create_patch()
        resp = self._test_update(person=person, patch=patch, submitter=person)
        self.assertEqual(4, PatchComment.objects.all().count())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(resp.data['addressed'])

    @utils.store_samples('patch-comment-detail-update-not-authorized')
    def test_update_not_authorized(self):
        """Update an existing patch comment when not signed in and not authorized.

        To be authorized users must meet at least one of the following:
        - project maintainer, patch submitter, patch delegate, or
          patch comment submitter

        Ensure updates can only be performed by authorized users.
        """
        person = create_person(user=self.user)
        resp = self._test_update(person=person, authenticate=False)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        person = create_person()  # normal user without edit permissions
        resp = self._test_update(person=person)  # signed-in
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('patch-comment-detail-update-error-bad-request')
    def test_update_invalid_addressed(self):
        """Update an existing patch comment using invalid values.

        Ensure we handle invalid patch comment addressed values.
        """
        person = create_person(name='patch-submitter', user=create_user())
        patch = create_patch(submitter=person)
        resp = self._test_update(person=person,
                                 patch=patch,
                                 addressed='not-valid',
                                 validate_request=False)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertFalse(
            getattr(PatchComment.objects.all().first(), 'addressed')
        )

    def test_create_delete(self):
        """Ensure creates and deletes aren't allowed"""
        comment = create_patch_comment(patch=self.patch)
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        resp = self.client.post(self.api_url(self.patch, item=comment))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(self.patch, item=comment))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
