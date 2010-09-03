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

import unittest
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from patchwork.models import Patch, Person, State
from patchwork.tests.utils import defaults, create_maintainer, find_in_context

class MultipleUpdateTest(TestCase):
    def setUp(self):
        defaults.project.save()
        self.user = create_maintainer(defaults.project)
        self.client.login(username = self.user.username,
                password = self.user.username)
        self.patches = []
        for name in ['patch one', 'patch two', 'patch three']:
            patch = Patch(project = defaults.project, msgid = name,
                            name = name, content = '',
                            submitter = Person.objects.get(user = self.user))
            patch.save()
            self.patches.append(patch)
        
    def _testStateChange(self, state):
        data = {'action':   'Update',
                'project':  str(defaults.project.id),
                'form':     'patchlistform',
                'archived': '*',
                'delegate': '*',
                'state':    str(state),
        }
        for patch in self.patches:
            data['patch_id:%d' % patch.id] = 'checked'

        url = reverse('patchwork.views.patch.list',
                args = [defaults.project.linkname])
        response = self.client.post(url, data)
        self.failUnlessEqual(response.status_code, 200)
        return response

    def testStateChangeValid(self):
        states = [patch.state.pk for patch in self.patches]
        state = State.objects.exclude(pk__in = states)[0]
        self._testStateChange(state.pk)
        for patch in [Patch.objects.get(pk = p.pk) for p in self.patches]:
            self.assertEquals(patch.state, state)

    def testStateChangeInvalid(self):
        state = max(State.objects.all().values_list('id', flat = True)) + 1
        orig_states = [patch.state for patch in self.patches]
        response = self._testStateChange(state)
        self.assertEquals( \
                [Patch.objects.get(pk = p.pk).state for p in self.patches],
                orig_states)
        self.assertEquals(response.context['errors'],
                    ['The submitted form data was invalid'])

    def testDelegateChange(self):
        delegate = create_maintainer(defaults.project)
        data = {'action':   'Update',
                'project':  str(defaults.project.id),
                'form':     'patchlistform',
                'archived': '*',
                'state':    '*',
                'delegate': str(delegate.pk),
        }
        for patch in self.patches:
            data['patch_id:%d' % patch.id] = 'checked'

        url = reverse('patchwork.views.patch.list',
                args = [defaults.project.linkname])
        response = self.client.post(url, data)
        self.failUnlessEqual(response.status_code, 200)
        for patch in [Patch.objects.get(pk = p.pk) for p in self.patches]:
            self.assertEquals(patch.delegate, delegate)

    def tearDown(self):
        for p in self.patches:
            p.delete()

