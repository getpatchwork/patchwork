# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.models import Patch
from patchwork.models import State
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_maintainer


class MultipleUpdateTest(TestCase):

    properties_form_id = 'patchform-properties'

    def setUp(self):
        self.project = create_project()
        self.user = create_maintainer(self.project)
        self.patches = create_patches(3, project=self.project)

        self.client.login(username=self.user.username,
                          password=self.user.username)

        self.url = reverse('patch-list', args=[self.project.linkname])
        self.base_data = {
            'action': 'Update',
            'project': str(self.project.id),
            'form': 'patchlistform',
            'archived': '*',
            'delegate': '*',
            'state': '*'
        }

    def _select_all_patches(self, data):
        for patch in self.patches:
            data['patch_id:%d' % patch.id] = 'checked'

    def test_archiving_patches(self):
        data = self.base_data.copy()
        data.update({'archived': 'True'})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, 'No patches to display',
                            status_code=200)
        # Don't use the cached version of patches: retrieve from the DB
        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertTrue(patch.archived)

    def test_unarchiving_patches(self):
        # Start with one patch archived and the remaining ones unarchived.
        self.patches[0].archived = True
        self.patches[0].save()

        data = self.base_data.copy()
        data.update({'archived': 'False'})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id,
                            status_code=200)
        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertFalse(patch.archived)

    def _test_state_change(self, state):
        data = self.base_data.copy()
        data.update({'state': str(state)})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id,
                            status_code=200)
        return response

    def test_state_change_valid(self):
        state = create_state()

        self._test_state_change(state.pk)

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.state, state)

    def test_state_change_invalid(self):
        state = max(State.objects.all().values_list('id', flat=True)) + 1
        orig_states = [patch.state for patch in self.patches]

        response = self._test_state_change(state)

        new_states = [Patch.objects.get(pk=p.pk).state for p in self.patches]
        self.assertEqual(new_states, orig_states)
        self.assertFormError(response, 'patchform', 'state',
                             'Select a valid choice. That choice is not one '
                             'of the available choices.')

    def _test_delegate_change(self, delegate_str):
        data = self.base_data.copy()
        data.update({'delegate': delegate_str})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id, status_code=200)
        return response

    def test_delegate_change_valid(self):
        delegate = create_maintainer(self.project)

        self._test_delegate_change(str(delegate.pk))

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.delegate, delegate)

    def test_delegate_clear(self):
        self._test_delegate_change('')

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.delegate, None)
