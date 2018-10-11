# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email.parser
from email.utils import make_msgid
import unittest

from django.conf import settings
from django.urls import reverse

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

    def test_list(self):
        """Validate we can list a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        person_obj = create_person(email='test@example.com')
        project_obj = create_project(linkname='myproject')
        state_obj = create_state(name='Under Review')
        patch_obj = create_patch(state=state_obj, project=project_obj,
                                 submitter=person_obj)

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertSerialized(patch_obj, patch_rsp)
        self.assertNotIn('headers', patch_rsp)
        self.assertNotIn('content', patch_rsp)
        self.assertNotIn('diff', patch_rsp)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertSerialized(patch_obj, patch_rsp)

        # test filtering by state
        resp = self.client.get(self.api_url(), {'state': 'under-review'})
        self.assertEqual([patch_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'state': 'missing-state'})
        self.assertEqual(0, len(resp.data))

        # test filtering by project
        resp = self.client.get(self.api_url(), {'project': 'myproject'})
        self.assertEqual([patch_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

        # test filtering by submitter, both ID and email
        resp = self.client.get(self.api_url(), {'submitter': person_obj.id})
        self.assertEqual([patch_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.com'})
        self.assertEqual([patch_obj.id], [x['id'] for x in resp.data])
        resp = self.client.get(self.api_url(), {
            'submitter': 'test@example.org'})
        self.assertEqual(0, len(resp.data))

        state_obj_b = create_state(name='New')
        create_patch(state=state_obj_b)
        state_obj_c = create_state(name='RFC')
        create_patch(state=state_obj_c)

        resp = self.client.get(self.api_url())
        self.assertEqual(3, len(resp.data))
        resp = self.client.get(self.api_url(), [('state', 'under-review')])
        self.assertEqual(1, len(resp.data))
        resp = self.client.get(self.api_url(), [('state', 'under-review'),
                                                ('state', 'new')])
        self.assertEqual(2, len(resp.data))

    def test_list_version_1_0(self):
        create_patch()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('url', resp.data[0])
        self.assertNotIn('web_url', resp.data[0])

    def test_detail(self):
        """Validate we can get a specific patch."""
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

    def test_update(self):
        """Ensure updates can be performed by maintainers."""
        project = create_project()
        patch = create_patch(project=project)
        state = create_state()

        # anonymous user
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # maintainer
        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {
            'state': state.name, 'delegate': user.id})
        self.assertEqual(status.HTTP_200_OK, resp.status_code, resp)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)
        # TODO(stephenfin): This is currently broken due to #216
        # self.assertEqual(Patch.objects.get(id=patch.id).delegate, user)

    def test_update_invalid(self):
        """Ensure we handle invalid Patch updates."""
        project = create_project()
        state = create_state()
        patch = create_patch(project=project, state=state)
        user = create_maintainer(project)

        # invalid state
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': 'foobar'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertContains(resp, 'Expected one of: %s.' % state.name,
                            status_code=status.HTTP_400_BAD_REQUEST)

        # invalid delegate
        user_b = create_user()
        resp = self.client.patch(self.api_url(patch.id),
                                 {'delegate': user_b.id})
        # TODO(stephenfin): This is currently broken due to #216
        # self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        # self.assertContains(resp, "User '%s' is not a maintainer" % user_b,
        #                     status_code=status.HTTP_400_BAD_REQUEST)

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
