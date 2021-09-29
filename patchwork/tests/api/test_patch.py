# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser
from email.utils import make_msgid
import unittest

import django
from django.conf import settings
from django.urls import NoReverseMatch
from django.urls import reverse

from patchwork.models import Patch
from patchwork.tests.api import utils
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status

# a diff different from the default, required to test hash filtering
SAMPLE_DIFF = """--- /dev/null\t2019-01-01 00:00:00.000000000 +0800
+++ a\t2019-01-01 00:00:00.000000000 +0800
@@ -0,0 +1 @@
+b
"""


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchAPI(utils.APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-patch-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-patch-detail', kwargs=kwargs)

    def assertSerialized(self, patch_obj, patch_json):
        self.assertEqual(patch_obj.id, patch_json['id'])
        self.assertEqual(patch_obj.name, patch_json['name'])
        self.assertEqual(patch_obj.msgid, patch_json['msgid'])
        self.assertEqual(patch_obj.state.slug, patch_json['state'])
        self.assertIn(patch_obj.get_mbox_url(), patch_json['mbox'])
        self.assertIn(patch_obj.get_absolute_url(), patch_json['web_url'])
        self.assertIn('comments', patch_json)

        # nested fields

        self.assertEqual(patch_obj.submitter.id,
                         patch_json['submitter']['id'])
        self.assertEqual(patch_obj.project.id,
                         patch_json['project']['id'])

        if patch_obj.series:
            self.assertEqual(1, len(patch_json['series']))
            self.assertEqual(patch_obj.series.id,
                             patch_json['series'][0]['id'])
        else:
            self.assertEqual([], patch_json['series'])

    def test_list_empty(self):
        """List patches when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def _create_patch(self, **kwargs):
        person_obj = create_person(email='test@example.com')
        project_obj = create_project(linkname='myproject')
        state_obj = create_state(name='Under Review')
        patch_obj = create_patch(state=state_obj, project=project_obj,
                                 submitter=person_obj, **kwargs)

        return patch_obj

    def test_list_anonymous(self):
        """List patches as anonymous user."""
        # we specifically set series to None to test code that handles legacy
        # patches created before series existed
        patch = self._create_patch(series=None)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertSerialized(patch, patch_rsp)
        self.assertNotIn('headers', patch_rsp)
        self.assertNotIn('content', patch_rsp)
        self.assertNotIn('diff', patch_rsp)

    @utils.store_samples('patch-list')
    def test_list_authenticated(self):
        """List patches as an authenticated user."""
        patch = self._create_patch()
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertSerialized(patch, patch_rsp)

    def test_list_filter_state(self):
        """Filter patches by state."""
        self._create_patch()
        user = create_user()

        state_obj_b = create_state(name='New')
        create_patch(state=state_obj_b)
        state_obj_c = create_state(name='RFC')
        create_patch(state=state_obj_c)

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url(), [('state', 'under-review'),
                                                ('state', 'new')])
        self.assertEqual(2, len(resp.data))

    def test_list_filter_project(self):
        """Filter patches by project."""
        patch = self._create_patch()
        user = create_user()

        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([patch.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_submitter(self):
        """Filter patches by submitter."""
        patch = self._create_patch()
        submitter = patch.submitter
        user = create_user()

        self.client.force_authenticate(user=user)

        # test filtering by submitter, both ID and email
        resp = self.client.get(self.api_url(), {'submitter': submitter.id})
        self.assertEqual([patch.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.com'})
        self.assertEqual([patch.id], [x['id'] for x in resp.data])

        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.org'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_hash(self):
        """Filter patches by hash."""
        patch = self._create_patch()
        patch_new_diff = create_patch(state=patch.state, project=patch.project,
                                      submitter=patch.submitter,
                                      diff=SAMPLE_DIFF)

        # check regular filtering
        resp = self.client.get(self.api_url(), {'hash': patch.hash})
        self.assertEqual([patch.id], [x['id'] for x in resp.data])

        # 2 patches with identical diffs
        patch_same_diff = create_patch(state=patch.state,
                                       project=patch.project,
                                       submitter=patch.submitter)
        resp = self.client.get(self.api_url(), {'hash': patch.hash})
        self.assertEqual([patch.id, patch_same_diff.id],
                         [x['id'] for x in resp.data])

        # case insensitive matching
        resp = self.client.get(self.api_url(),
                               {'hash': patch_new_diff.hash.upper()})
        self.assertEqual([patch_new_diff.id], [x['id'] for x in resp.data])

        # empty response if nothing matches
        resp = self.client.get(self.api_url(), {
            'hash': 'da638d0746a115000bf890fada1f02679aa282e8'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_hash_version_1_1(self):
        """Filter patches by hash using API v1.1."""
        self._create_patch()

        # we still see the patch since the hash field is ignored
        resp = self.client.get(self.api_url(version='1.1'),
                               {'hash': 'garbagevalue'})
        self.assertEqual(1, len(resp.data))

    def test_list_filter_msgid(self):
        """Filter patches by msgid."""
        patch = self._create_patch()

        resp = self.client.get(self.api_url(), {'msgid': patch.url_msgid})
        self.assertEqual([patch.id], [x['id'] for x in resp.data])

        # empty response if nothing matches
        resp = self.client.get(self.api_url(), {
            'msgid': 'fishfish@fish.fish'})
        self.assertEqual(0, len(resp.data))

    @utils.store_samples('patch-list-1-0')
    def test_list_version_1_0(self):
        """List patches using API v1.0."""
        create_patch()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_list_bug_335(self):
        """Ensure we retrieve the embedded series project in O(1)."""
        series = create_series()
        create_patches(5, series=series)

        # TODO(stephenfin): Remove when we drop support for Django < 3.2
        num_queries = 7 if django.VERSION < (3, 2) else 5

        with self.assertNumQueries(num_queries):
            self.client.get(self.api_url())

    @utils.store_samples('patch-detail')
    def test_detail(self):
        """Show a specific patch."""
        patch = create_patch(
            content='Reviewed-by: Test User <test@example.com>\n',
            headers='Received: from somewhere\nReceived: from another place'
        )

        resp = self.client.get(self.api_url(patch.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(patch, resp.data)

        # Make sure we don't regress and all headers with the same key are
        # included in the response
        parsed_headers = email.parser.Parser().parsestr(patch.headers, True)
        for key, value in parsed_headers.items():
            self.assertIn(value, resp.data['headers'][key])

        self.assertEqual(patch.content, resp.data['content'])
        self.assertEqual(patch.diff, resp.data['diff'])
        self.assertEqual(0, len(resp.data['tags']))

    @utils.store_samples('patch-detail-1-0')
    def test_detail_version_1_0(self):
        patch = create_patch()

        resp = self.client.get(self.api_url(item=patch.id, version='1.0'))
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)
        self.assertNotIn('comments', resp.data)

    def test_detail_non_existent(self):
        """Ensure we get a 404 for a non-existent patch."""
        resp = self.client.get(self.api_url('999999'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_detail_invalid(self):
        """Ensure we get a 404 for an invalid patch ID."""
        with self.assertRaises(NoReverseMatch):
            self.client.get(self.api_url('foo'))

    def test_create(self):
        """Ensure creations are rejected."""
        project = create_project()
        patch = {
            'project': project.id,
            'submitter': create_person().id,
            'msgid': make_msgid(),
            'name': 'test-create-patch',
            'diff': 'patch diff',
        }

        # anonymous user
        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    @utils.store_samples('patch-update-error-forbidden')
    def test_update_anonymous(self):
        """Update patch as anonymous user.

        Ensure updates can be performed by maintainers.
        """
        patch = create_patch()
        state = create_state()

        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_update_non_maintainer(self):
        """Update patch as non-maintainer.

        Ensure updates can be performed by maintainers.
        """
        patch = create_patch()
        state = create_state()
        user = create_user()

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('patch-update')
    def test_update_maintainer(self):
        """Update patch as maintainer.

        Ensure updates can be performed by maintainers.
        """
        project = create_project()
        patch = create_patch(project=project)
        state = create_state()
        user = create_maintainer(project)

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id),
                                 {'state': state.slug, 'delegate': user.id})
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)
        self.assertEqual(Patch.objects.get(id=patch.id).delegate, user)

        # (who can unset fields too)
        # we need to send as JSON due to https://stackoverflow.com/q/30677216/
        resp = self.client.patch(self.api_url(patch.id), {'delegate': None},
                                 format='json')
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertIsNone(Patch.objects.get(id=patch.id).delegate)

    def test_update_maintainer_version_1_0(self):
        """Update patch as maintainer on v1.1."""
        project = create_project()
        patch = create_patch(project=project)
        state = create_state()
        user = create_maintainer(project)

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id, version="1.1"),
                                 {'state': state.slug, 'delegate': user.id})
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)
        self.assertEqual(Patch.objects.get(id=patch.id).delegate, user)

    @utils.store_samples('patch-update-error-bad-request')
    def test_update_invalid_state(self):
        """Update patch with invalid fields.

        Ensure we handle invalid Patch updates.
        """
        project = create_project()
        state = create_state()
        patch = create_patch(project=project, state=state)
        user = create_maintainer(project)

        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': 'foobar'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertContains(resp, 'Expected one of: %s.' % state.slug,
                            status_code=status.HTTP_400_BAD_REQUEST)

    def test_update_legacy_delegate(self):
        """Regression test for bug #313."""
        project = create_project()
        state = create_state()
        patch = create_patch(project=project, state=state)
        user_a = create_maintainer(project)

        # create a user (User), then delete the associated UserProfile and save
        # the user to ensure a new profile is generated
        user_b = create_user()
        self.assertEqual(user_b.id, user_b.profile.id)
        user_b.profile.delete()
        user_b.save()
        user_b.profile.maintainer_projects.add(project)
        user_b.profile.save()
        self.assertNotEqual(user_b.id, user_b.profile.id)

        self.client.force_authenticate(user=user_a)
        resp = self.client.patch(self.api_url(patch.id),
                                 {'delegate': user_b.id})
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)
        self.assertEqual(Patch.objects.get(id=patch.id).delegate, user_b)

    def test_update_invalid_delegate(self):
        """Update patch with invalid fields.

        Ensure we handle invalid Patch updates.
        """
        project = create_project()
        state = create_state()
        patch = create_patch(project=project, state=state)
        user_a = create_maintainer(project)
        user_b = create_user()

        self.client.force_authenticate(user=user_a)
        resp = self.client.patch(self.api_url(patch.id),
                                 {'delegate': user_b.id})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertContains(resp, "User '%s' is not a maintainer" % user_b,
                            status_code=status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        """Ensure deletions are always rejected."""
        project = create_project()
        patch = create_patch(project=project)

        # anonymous user
        resp = self.client.delete(self.api_url(patch.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(patch.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
