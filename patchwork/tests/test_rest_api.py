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
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from patchwork.models import Check, Patch, Project
from patchwork.tests.utils import (
    defaults, create_maintainer, create_user, create_patches, make_msgid)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestProjectAPI(APITestCase):
    fixtures = ['default_states']

    def setUp(self):
        self.project = defaults.project
        self.project.save()

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api_1.0:project-list')
        return reverse('api_1.0:project-detail', args=[item])

    def test_list_simple(self):
        """Validate we can list the default test project."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        proj = resp.data[0]
        self.assertEqual(self.project.linkname, proj['link_name'])
        self.assertEqual(self.project.name, proj['name'])
        self.assertEqual(self.project.listid, proj['list_id'])

    def test_detail(self):
        """Validate we can get a specific project."""
        resp = self.client.get(self.api_url(self.project.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(self.project.name, resp.data['name'])

        # make sure we can look up by linkname
        resp = self.client.get(self.api_url(resp.data['link_name']))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(defaults.project.name, resp.data['name'])

    def test_get_numeric_linkname(self):
        """Validate we try to do the right thing for numeric linkname"""
        project = Project(linkname='12345', name='Test Project',
                          listid='test.example.com')
        project.save()
        resp = self.client.get(self.api_url('12345'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(project.name, resp.data['name'])

    def test_anonymous_create(self):
        """Ensure anonymous POST operations are rejected."""
        resp = self.client.post(
            self.api_url(),
            {'linkname': 'l', 'name': 'n', 'listid': 'l', 'listemail': 'e'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous_update(self):
        """Ensure anonymous "PATCH" operations are rejected."""
        resp = self.client.patch(self.api_url(self.project.id),
                                 {'linkname': 'foo'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous_delete(self):
        """Ensure anonymous "DELETE" operations are rejected."""
        resp = self.client.delete(self.api_url(self.project.id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create(self):
        """Ensure creations are rejected."""
        user = create_maintainer(self.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post(
            self.api_url(),
            {'linkname': 'l', 'name': 'n', 'listid': 'l', 'listemail': 'e'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_update(self):
        """Ensure updates can be performed maintainers."""
        # A maintainer can update
        user = create_maintainer(self.project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(self.project.id),
                                 {'linkname': 'TEST'})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

        # A normal user can't
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(self.project.id),
                                 {'linkname': 'TEST'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_delete(self):
        """Ensure deletions are rejected."""
        # Even an admin can't remove a project
        user = create_maintainer(self.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(self.project.id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertEqual(1, Project.objects.all().count())


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPersonAPI(APITestCase):
    fixtures = ['default_states']

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api_1.0:person-list')
        return reverse('api_1.0:person-detail', args=[item])

    def test_anonymous_list(self):
        """The API should reject anonymous users."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_authenticated_list(self):
        """This API requires authenticated users."""
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(user.username, resp.data[0]['name'])
        self.assertEqual(user.email, resp.data[0]['email'])
        self.assertIn('users/%d/' % user.id, resp.data[0]['user_url'])

    def test_unlinked_user(self):
        defaults.patch_author_person.save()
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))
        self.assertEqual(defaults.patch_author_person.name,
                         resp.data[0]['name'])
        self.assertIsNone(resp.data[0]['user_url'])

    def test_readonly(self):
        defaults.project.save()
        user = create_maintainer(defaults.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        resp = self.client.patch(self.api_url(user.id),
                                 {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        resp = self.client.post(self.api_url(), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestUserAPI(APITestCase):
    fixtures = ['default_states']

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api_1.0:user-list')
        return reverse('api_1.0:user-detail', args=[item])

    def test_anonymous_list(self):
        """The API should reject anonymous users."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_authenticated_list(self):
        """This API requires authenticated users."""
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(user.username, resp.data[0]['username'])
        self.assertNotIn('password', resp.data[0])
        self.assertNotIn('is_superuser', resp.data[0])

    def test_readonly(self):
        defaults.project.save()
        user = create_maintainer(defaults.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.delete(self.api_url(1))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        resp = self.client.patch(self.api_url(1), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        resp = self.client.post(self.api_url(), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchAPI(APITestCase):
    fixtures = ['default_states', 'default_tags']

    def setUp(self):
        self.patches = create_patches()

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api_1.0:patch-list')
        return reverse('api_1.0:patch-detail', args=[item])

    def test_list_simple(self):
        """Validate we can list a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch = resp.data[0]
        self.assertEqual(self.patches[0].name, patch['name'])
        self.assertNotIn('content', patch)
        self.assertNotIn('headers', patch)
        self.assertNotIn('diff', patch)

        # test while authenticated
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch = resp.data[0]
        self.assertEqual(self.patches[0].name, patch['name'])

    def test_detail(self):
        """Validate we can get a specific project."""
        resp = self.client.get(self.api_url(self.patches[0].id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(self.patches[0].name, resp.data['name'])
        self.assertIn(TestProjectAPI.api_url(self.patches[0].project.id),
                      resp.data['project_url'])
        self.assertEqual(self.patches[0].msgid, resp.data['msgid'])
        self.assertEqual(self.patches[0].diff, resp.data['diff'])
        self.assertIn(TestPersonAPI.api_url(self.patches[0].submitter.id),
                      resp.data['submitter_url'])
        self.assertEqual(self.patches[0].state.name, resp.data['state'])
        self.assertIn(self.patches[0].get_mbox_url(), resp.data['mbox_url'])

    def test_detail_tags(self):
        # defaults.project is remembered between TestCases and .save() is
        # called which just updates the object. This leaves the potential for
        # the @cached_property project.tags to be invalid, so we have to
        # invalidate this cached value before doing tag operations:
        del defaults.project.tags

        self.patches[0].content = 'Reviewed-by: Test User <test@example.com>\n'
        self.patches[0].save()
        resp = self.client.get(self.api_url(self.patches[0].id))
        tags = resp.data['tags']
        self.assertEqual(1, len(tags))
        self.assertEqual(1, tags[0]['count'])
        self.assertEqual('Reviewed-by', tags[0]['name'])

    def test_anonymous_create(self):
        """Ensure anonymous "POST" operations are rejected."""
        patch = {
            'project': defaults.project.id,
            'submitter': defaults.patch_author_person.id,
            'msgid': make_msgid(),
            'name': 'test-create-patch',
            'diff': 'patch diff',
        }

        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous_update(self):
        """Ensure anonymous "PATCH" operations are rejected."""
        patch_url = self.api_url(self.patches[0].id)
        resp = self.client.get(patch_url)
        patch = resp.data
        patch['msgid'] = 'foo'
        patch['name'] = 'this should fail'

        resp = self.client.patch(patch_url, {'name': 'foo'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous_delete(self):
        """Ensure anonymous "DELETE" operations are rejected."""
        patch_url = self.api_url(self.patches[0].id)
        resp = self.client.get(patch_url)

        resp = self.client.delete(patch_url)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create(self):
        """Ensure creations are rejected."""
        patch = {
            'project': defaults.project.id,
            'submitter': defaults.patch_author_person.id,
            'msgid': make_msgid(),
            'name': 'test-create-patch',
            'diff': 'patch diff',
        }

        user = create_maintainer(defaults.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_update(self):
        """Ensure updates can be performed maintainers."""
        # A maintainer can update
        user = create_maintainer(defaults.project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(self.patches[0].id),
                                 {'state': 2})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

        # A normal user can't
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(self.patches[0].id),
                                 {'state': 2})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_delete(self):
        """Ensure deletions are rejected."""
        user = create_maintainer(defaults.project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(self.patches[0].id))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertEqual(1, Patch.objects.all().count())


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCheckAPI(APITestCase):
    fixtures = ['default_states', 'default_tags']

    def setUp(self):
        super(TestCheckAPI, self).setUp()
        self.patch = create_patches()[0]
        self.urlbase = reverse('api_1.0:patch-detail', args=[self.patch.id])
        self.urlbase += 'checks/'
        defaults.project.save()
        self.user = create_maintainer(defaults.project)

    def create_check(self):
        return Check.objects.create(patch=self.patch, user=self.user,
                                    state=Check.STATE_WARNING, target_url='t',
                                    description='d', context='c')

    def test_list_simple(self):
        """Validate we can list checks on a patch."""
        resp = self.client.get(self.urlbase)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        c = self.create_check()
        resp = self.client.get(self.urlbase)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        check = resp.data[0]
        self.assertEqual(c.get_state_display(), check['state'])
        self.assertEqual(c.target_url, check['target_url'])
        self.assertEqual(c.context, check['context'])
        self.assertEqual(c.description, check['description'])

    def test_detail(self):
        """Validate we can get a specific check."""
        c = self.create_check()
        resp = self.client.get(self.urlbase + str(c.id) + '/')
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(c.target_url, resp.data['target_url'])

    def test_update_delete(self):
        """Ensure updates and deletes aren't allowed"""
        c = self.create_check()

        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        # update
        resp = self.client.patch(
            self.urlbase + str(c.id) + '/', {'target_url': 'fail'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        # delete
        resp = self.client.delete(self.urlbase + str(c.id) + '/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create(self):
        """Ensure creations can be performed by user of patch."""
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.urlbase, check)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())

        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.urlbase, check)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create_invalid(self):
        """Ensure we handle invalid check states"""
        check = {
            'state': 'this-is-not-a-valid-state',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.urlbase, check)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())
