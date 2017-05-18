# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

from django.test import TestCase

from patchwork.compat import reverse
from patchwork.tests import utils


class ProjectViewTest(TestCase):

    def test_redirect(self):
        project = utils.create_project()

        requested_url = reverse('project-list')
        redirect_url = reverse('patch-list', kwargs={
            'project_id': project.linkname})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_no_redirect(self):
        utils.create_project()
        utils.create_project()

        requested_url = reverse('project-list')

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 2)

    def test_n_patches(self):
        project = utils.create_project()

        requested_url = reverse('project-detail', kwargs={
            'project_id': project.linkname})

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['n_patches'], 0)
        self.assertEqual(response.context['n_archived_patches'], 0)

        utils.create_patch(project=project)

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['n_patches'], 1)
        self.assertEqual(response.context['n_archived_patches'], 0)

        utils.create_patch(project=project, archived=True)

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['n_patches'], 1)
        self.assertEqual(response.context['n_archived_patches'], 1)

    def test_maintainers(self):
        project = utils.create_project()

        requested_url = reverse('project-detail', kwargs={
            'project_id': project.linkname})

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['maintainers']), 0)

        utils.create_maintainer(project=project)

        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['maintainers']), 1)
