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

from patchwork.models import Project
from patchwork.tests.utils import defaults, create_maintainer, create_user


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
