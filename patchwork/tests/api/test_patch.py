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

import email.parser
from email.utils import make_msgid
import unittest

from django.conf import settings

from patchwork.compat import reverse
from patchwork.models import Patch
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchAPI(APITestCase):
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

    def test_list_empty(self):
        """List patches when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def _create_patch(self):
        person_obj = create_person(email='test@example.com')
        project_obj = create_project(linkname='myproject')
        state_obj = create_state(name='Under Review')
        patch_obj = create_patch(state=state_obj, project=project_obj,
                                 submitter=person_obj)

        return patch_obj

    def test_list_anonymous(self):
        """List patches as anonymous user."""
        patch = self._create_patch()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertSerialized(patch, patch_rsp)
        self.assertNotIn('headers', patch_rsp)
        self.assertNotIn('content', patch_rsp)
        self.assertNotIn('diff', patch_rsp)

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

    def test_list_version_1_0(self):
        """List patches using API v1.0."""
        create_patch()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

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

    def test_detail_version_1_0(self):
        patch = create_patch()

        resp = self.client.get(self.api_url(item=patch.id, version='1.0'))
        self.assertIn('url', resp.data)
        self.assertNotIn('web_url', resp.data)
        self.assertNotIn('comments', resp.data)

    def test_create(self):
        """Ensure creations are rejected."""
        project = create_project()
        patch = {
            'project': project,
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
                                 {'state': state.name, 'delegate': user.id})
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)
        self.assertEqual(Patch.objects.get(id=patch.id).delegate, user)

        # (who can unset fields too)
        # we need to send as JSON due to https://stackoverflow.com/q/30677216/
        resp = self.client.patch(self.api_url(patch.id), {'delegate': None},
                                 format='json')
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertIsNone(Patch.objects.get(id=patch.id).delegate)

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
        self.assertContains(resp, 'Expected one of: %s.' % state.name,
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
