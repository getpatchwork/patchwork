# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

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
