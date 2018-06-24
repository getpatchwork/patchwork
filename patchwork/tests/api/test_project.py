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
from django.urls import reverse

from patchwork.models import Project
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
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
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-project-list', kwargs=kwargs)
        return reverse('api-project-detail', args=[item], kwargs=kwargs)

    def assertSerialized(self, project_obj, project_json):
        self.assertEqual(project_obj.id, project_json['id'])
        self.assertEqual(project_obj.name, project_json['name'])
        self.assertEqual(project_obj.linkname, project_json['link_name'])
        self.assertEqual(project_obj.listid, project_json['list_id'])
        self.assertEqual(project_obj.subject_match,
                         project_json['subject_match'])

        # nested fields

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

        # test old version of API
        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertNotIn('subject_match', resp.data[0])

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

    def test_get_by_id(self):
        """Validate that it's possible to filter by pk."""
        project = create_project()

        resp = self.client.get(self.api_url(project.pk))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    def test_get_by_linkname(self):
        """Validate that it's possible to filter by linkname."""
        project = create_project(linkname='project', name='Sample project')

        resp = self.client.get(self.api_url('project'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    def test_get_by_numeric_linkname(self):
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
