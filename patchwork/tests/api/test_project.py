# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.models import Project
from patchwork.tests.api import utils
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestProjectAPI(utils.APITestCase):

    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-project-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-project-detail', kwargs=kwargs)

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

    def test_list_empty(self):
        """List projects when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def test_list_anonymous(self):
        """List projects as anonymous user."""
        project = create_project()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(project, resp.data[0])

    @utils.store_samples('project-list')
    def test_list_authenticated(self):
        """List projects as an authenticated user."""
        project = create_project()
        user = create_maintainer(project)

        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertSerialized(project, resp.data[0])
        self.assertIn('subject_match', resp.data[0])
        self.assertIn('list_archive_url', resp.data[0])
        self.assertIn('list_archive_url_format', resp.data[0])
        self.assertIn('commit_url_format', resp.data[0])

    @utils.store_samples('project-list-1.1')
    def test_list_version_1_1(self):
        """List projects using API v1.1.

        Validate that newer fields are dropped for older API versions.
        """
        create_project()

        resp = self.client.get(self.api_url(version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertIn('subject_match', resp.data[0])
        self.assertNotIn('list_archive_url', resp.data[0])
        self.assertNotIn('list_archive_url_format', resp.data[0])
        self.assertNotIn('commit_url_format', resp.data[0])

    @utils.store_samples('project-list-1.0')
    def test_list_version_1_0(self):
        """List projects using API v1.0.

        Validate that newer fields are dropped for older API versions.
        """
        create_project()

        resp = self.client.get(self.api_url(version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertNotIn('subject_match', resp.data[0])

    @utils.store_samples('project-detail')
    def test_detail(self):
        """Show project using ID lookup.

        Validate that it's possible to filter by pk.
        """
        project = create_project()

        resp = self.client.get(self.api_url(project.pk))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)
        self.assertIn('subject_match', resp.data)
        self.assertIn('list_archive_url', resp.data)
        self.assertIn('list_archive_url_format', resp.data)
        self.assertIn('commit_url_format', resp.data)

    def test_detail_by_linkname(self):
        """Show project using linkname lookup.

        Validate that it's possible to filter by linkname.
        """
        project = create_project(linkname='project', name='Sample project')

        resp = self.client.get(self.api_url('project'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    def test_detail_by_numeric_linkname(self):
        """Show project using numeric linkname lookup.

        Validate we try to do the right thing for numeric linkname.
        """
        project = create_project(linkname='12345')

        resp = self.client.get(self.api_url('12345'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertSerialized(project, resp.data)

    @utils.store_samples('project-detail-1.1')
    def test_detail_version_1_1(self):
        """Show project using API v1.1.

        Validate that newer fields are dropped for older API versions.
        """
        project = create_project()

        resp = self.client.get(self.api_url(project.pk, version='1.1'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertIn('name', resp.data)
        self.assertIn('subject_match', resp.data)
        self.assertNotIn('list_archive_url', resp.data)
        self.assertNotIn('list_archive_url_format', resp.data)
        self.assertNotIn('commit_url_format', resp.data)

    @utils.store_samples('project-detail-1.0')
    def test_detail_version_1_0(self):
        """Show project using API v1.0.

        Validate that newer fields are dropped for older API versions.
        """
        project = create_project()

        resp = self.client.get(self.api_url(project.pk, version='1.0'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertIn('name', resp.data)
        self.assertNotIn('subject_match', resp.data)

    def test_detail_non_existent(self):
        """Ensure we get a 404 for a non-existent project."""
        resp = self.client.get(self.api_url('999999'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

        resp = self.client.get(self.api_url('foo'))
        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

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

    def test_update_anonymous(self):
        """Update project as anonymous user.

        Ensure updates can only be performed by maintainers.
        """
        project = create_project()
        data = {'web_url': 'https://example.com/test'}

        # an anonymous user
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('project-update-error-forbidden')
    def test_update_non_maintainer(self):
        """Update project as normal user.

        Ensure updates can only be performed by maintainers.
        """
        project = create_project()
        data = {'web_url': 'https://example.com/test'}

        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    @utils.store_samples('project-update')
    def test_update_maintainer(self):
        """Update project as maintainer.

        Ensure updates can only be performed by maintainers.
        """
        project = create_project()
        data = {'web_url': 'https://example.com/test'}

        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(resp.data['web_url'], 'https://example.com/test')

    def test_update_readonly_field(self):
        """Update read-only fields."""
        project = create_project()

        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(
            self.api_url(project.id),
            {'link_name': 'test'},
            validate_request=False,
        )
        # NOTE(stephenfin): This actually returns HTTP 200 due to
        # https://github.com/encode/django-rest-framework/issues/1655
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertNotEqual(resp.data['link_name'], 'test')

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
