# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
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

from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.models import Patch, Person, State
from patchwork.tests.utils import defaults, create_maintainer


class MultipleUpdateTest(TestCase):
    fixtures = ['default_states']

    def setUp(self):
        defaults.project.save()
        self.user = create_maintainer(defaults.project)
        self.client.login(username = self.user.username,
                password = self.user.username)
        self.properties_form_id = 'patchform-properties'
        self.url = reverse(
            'patchwork.views.patch.list', args = [defaults.project.linkname])
        self.base_data = {
            'action': 'Update', 'project': str(defaults.project.id),
            'form': 'patchlistform', 'archived': '*', 'delegate': '*',
            'state': '*'}
        self.patches = []
        for name in ['patch one', 'patch two', 'patch three']:
            patch = Patch(project = defaults.project, msgid = name,
                            name = name, content = '',
                            submitter = Person.objects.get(user = self.user))
            patch.save()
            self.patches.append(patch)

    def _selectAllPatches(self, data):
        for patch in self.patches:
            data['patch_id:%d' % patch.id] = 'checked'

    def testArchivingPatches(self):
        data = self.base_data.copy()
        data.update({'archived': 'True'})
        self._selectAllPatches(data)
        response = self.client.post(self.url, data)
        self.assertContains(response, 'No patches to display',
                            status_code = 200)
        for patch in [Patch.objects.get(pk = p.pk) for p in self.patches]:
            self.assertTrue(patch.archived)

    def testUnArchivingPatches(self):
        # Start with one patch archived and the remaining ones unarchived.
        self.patches[0].archived = True
        self.patches[0].save()
        data = self.base_data.copy()
        data.update({'archived': 'False'})
        self._selectAllPatches(data)
        response = self.client.post(self.url, data)
        self.assertContains(response, self.properties_form_id,
                            status_code = 200)
        for patch in [Patch.objects.get(pk = p.pk) for p in self.patches]:
            self.assertFalse(patch.archived)

    def _testStateChange(self, state):
        data = self.base_data.copy()
        data.update({'state': str(state)})
        self._selectAllPatches(data)
        response = self.client.post(self.url, data)
        self.assertContains(response, self.properties_form_id,
                            status_code = 200)
        return response

    def testStateChangeValid(self):
        states = [patch.state.pk for patch in self.patches]
        state = State.objects.exclude(pk__in = states)[0]
        self._testStateChange(state.pk)
        for p in self.patches:
            self.assertEquals(Patch.objects.get(pk = p.pk).state, state)

    def testStateChangeInvalid(self):
        state = max(State.objects.all().values_list('id', flat = True)) + 1
        orig_states = [patch.state for patch in self.patches]
        response = self._testStateChange(state)
        self.assertEquals( \
                [Patch.objects.get(pk = p.pk).state for p in self.patches],
                orig_states)
        self.assertFormError(response, 'patchform', 'state',
                    'Select a valid choice. That choice is not one ' + \
                        'of the available choices.')

    def _testDelegateChange(self, delegate_str):
        data = self.base_data.copy()
        data.update({'delegate': delegate_str})
        self._selectAllPatches(data)
        response = self.client.post(self.url, data)
        self.assertContains(response, self.properties_form_id,
                            status_code=200)
        return response

    def testDelegateChangeValid(self):
        delegate = create_maintainer(defaults.project)
        response = self._testDelegateChange(str(delegate.pk))
        for p in self.patches:
            self.assertEquals(Patch.objects.get(pk = p.pk).delegate, delegate)

    def testDelegateClear(self):
        response = self._testDelegateChange('')
        for p in self.patches:
            self.assertEquals(Patch.objects.get(pk = p.pk).delegate, None)
