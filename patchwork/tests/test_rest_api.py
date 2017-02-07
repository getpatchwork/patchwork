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

from email.utils import make_msgid
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from patchwork.models import Check
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestProjectAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-project-list')
        return reverse('api-project-detail', args=[item])

    def assertSerialized(self, project_obj, project_json):
        self.assertEqual(project_obj.id, project_json['id'])
        self.assertEqual(project_obj.name, project_json['name'])
        self.assertEqual(project_obj.linkname, project_json['link_name'])
        self.assertEqual(project_obj.listid, project_json['list_id'])
        self.assertEqual(len(project_json['maintainers']),
                         project_obj.maintainer_project.all().count())

    def test_list(self):
        """Validate we can list the default test project."""
        project = create_project()

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(project, resp.data[0])

        # maintainer
        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(project, resp.data[0])

    def test_detail(self):
        """Validate we can get a specific project."""
        project = create_project()

        resp = self.client.get(self.api_url(project.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(project.name, resp.data['name'])

        # make sure we can look up by linkname
        resp = self.client.get(self.api_url(resp.data['link_name']))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    def test_get_numeric_linkname(self):
        """Validate we try to do the right thing for numeric linkname"""
        project = create_project(linkname='12345')

        resp = self.client.get(self.api_url('12345'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    def test_create(self):
        """Ensure creations are rejected."""
        project = create_project()
        data = {'linkname': 'l', 'name': 'n', 'listid': 'l', 'listemail': 'e'}

        # an anonymous user
        resp = self.client.post(self.api_url(), data)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # a superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), data)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_update(self):
        """Ensure updates can be performed by maintainers."""
        project = create_project()
        data = {'linkname': 'TEST'}

        # an anonymous user
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # a normal user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # a maintainer
        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

    def test_delete(self):
        """Ensure deletions are rejected."""
        project = create_project()

        # an anonymous user
        resp = self.client.delete(self.api_url(project.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # a super user
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(project.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
        self.assertEqual(1, Project.objects.all().count())


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
            self.assertIn(TestUserAPI.api_url(person_obj.user.id),
                          person_json['user'])

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


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchAPI(APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-patch-list')
        return reverse('api-patch-detail', args=[item])

    def assertSerialized(self, patch_obj, patch_json):
        self.assertEqual(patch_obj.id, patch_json['id'])
        self.assertEqual(patch_obj.name, patch_json['name'])
        self.assertEqual(patch_obj.msgid, patch_json['msgid'])
        self.assertEqual(patch_obj.state.name, patch_json['state'])
        self.assertIn(patch_obj.get_mbox_url(), patch_json['mbox'])
        self.assertIn(TestPersonAPI.api_url(patch_obj.submitter.id),
                      patch_json['submitter'])
        self.assertIn(TestProjectAPI.api_url(patch_obj.project.id),
                      patch_json['project'])

    def test_list(self):
        """Validate we can list a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        patch_obj = create_patch()

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

    def test_detail(self):
        """Validate we can get a specific patch."""
        patch = create_patch(
            content='Reviewed-by: Test User <test@example.com>\n')

        resp = self.client.get(self.api_url(patch.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(patch, resp.data)
        self.assertEqual(patch.headers, resp.data['headers'] or '')
        self.assertEqual(patch.content, resp.data['content'])
        self.assertEqual(patch.diff, resp.data['diff'])
        self.assertEqual(3, len(resp.data['tags']))
        self.assertEqual(1, resp.data['tags']['Reviewed-by'])

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
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(Patch.objects.get(id=patch.id).state, state)

    def test_update_invalid(self):
        """Ensure we handle invalid Patch states."""
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


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCoverLetterAPI(APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-cover-list')
        return reverse('api-cover-detail', args=[item])

    def assertSerialized(self, cover_obj, cover_json):
        self.assertEqual(cover_obj.id, cover_json['id'])
        self.assertEqual(cover_obj.name, cover_json['name'])
        self.assertIn(TestPersonAPI.api_url(cover_obj.submitter.id),
                      cover_json['submitter'])

    def test_list(self):
        """Validate we can list cover letters."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        cover_obj = create_cover()

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(cover_obj, resp.data[0])

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(cover_obj, resp.data[0])

    def test_detail(self):
        """Validate we can get a specific cover letter."""
        cover_obj = create_cover()

        resp = self.client.get(self.api_url(cover_obj.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(cover_obj, resp.data)

    def test_create_update_delete(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'name': 'test cover'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.patch(self.api_url(), {'name': 'test cover'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url())
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestSeriesAPI(APITestCase):
    fixtures = ['default_tags']

    def api_url(self, item=None):
        if item is None:
            return reverse('api-series-list')
        return reverse('api-series-detail', args=[item])

    def assertSerialized(self, series_obj, series_json):
        self.assertEqual(series_obj.id, series_json['id'])
        self.assertEqual(series_obj.name, series_json['name'])
        self.assertIn(TestProjectAPI.api_url(series_obj.project.id),
                      series_json['project'])
        self.assertIn(TestPersonAPI.api_url(series_obj.submitter.id),
                      series_json['submitter'])
        self.assertEqual(series_obj.patches.count(),
                         len(series_json['patches']))
        if series_obj.cover_letter:
            self.assertIn(
                TestCoverLetterAPI.api_url(series_obj.cover_letter.id),
                series_json['cover_letter'])

    def test_list(self):
        """Validate we can list series."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        series = create_series()

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(series, resp.data[0])

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(series, resp.data[0])

    def test_detail(self):
        """Validate we can get a specific series."""
        series = create_series()

        resp = self.client.get(self.api_url(series.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(series, resp.data)

        patch = create_patch(project=series.project)
        series.add_patch(patch, 1)
        resp = self.client.get(self.api_url(series.id))
        self.assertSerialized(series, resp.data)

        cover_letter = create_cover(project=series.project)
        series.add_cover_letter(cover_letter)
        resp = self.client.get(self.api_url(series.id))
        self.assertSerialized(series, resp.data)

    def test_create_update_delete(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'name': 'test series'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.patch(self.api_url(), {'name': 'test series'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url())
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCheckAPI(APITestCase):
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

    def _create_check(self):
        values = {
            'patch': self.patch,
            'user': self.user,
        }
        return create_check(**values)

    def assertSerialized(self, check_obj, check_json):
        self.assertEqual(check_obj.id, check_json['id'])
        self.assertEqual(check_obj.get_state_display(), check_json['state'])
        self.assertEqual(check_obj.target_url, check_json['target_url'])
        self.assertEqual(check_obj.context, check_json['context'])
        self.assertEqual(check_obj.description, check_json['description'])

    def test_list(self):
        """Validate we can list checks on a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        check_obj = self._create_check()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(check_obj, resp.data[0])

    def test_detail(self):
        """Validate we can get a specific check."""
        check = self._create_check()
        resp = self.client.get(self.api_url(check))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(check, resp.data)

    def test_create(self):
        """Ensure creations can be performed by user of patch."""
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())
        self.assertSerialized(Check.objects.first(), resp.data)

        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create_invalid(self):
        """Ensure we handle invalid check states."""
        check = {
            'state': 'this-is-not-a-valid-state',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())

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
