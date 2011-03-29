# Patchwork - automated patch tracking system
# Copyright (C) 2011 Jeremy Kerr <jk@ozlabs.org>
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
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from patchwork.models import Patch, State, PatchChangeNotification
from patchwork.tests.utils import defaults, create_maintainer

class PatchNotificationModelTest(TestCase):
    """Tests for the creation & update of the PatchChangeNotification model"""

    def setUp(self):
        self.project = defaults.project
        self.project.send_notifications = True
        self.project.save()
        self.submitter = defaults.patch_author_person
        self.submitter.save()
        self.patch = Patch(project = self.project, msgid = 'testpatch',
                        name = 'testpatch', content = '',
                        submitter = self.submitter)

    def tearDown(self):
        self.patch.delete()
        self.submitter.delete()
        self.project.delete()

    def testPatchCreation(self):
        """Ensure we don't get a notification on create"""
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def testPatchUninterestingChange(self):
        """Ensure we don't get a notification for "uninteresting" changes"""
        self.patch.save()
        self.patch.archived = True
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def testPatchChange(self):
        """Ensure we get a notification for interesting patch changes"""
        self.patch.save()
        oldstate = self.patch.state
        state = State.objects.exclude(pk = oldstate.pk)[0]

        self.patch.state = state
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.patch, self.patch)
        self.assertEqual(notification.orig_state, oldstate)

    def testNotificationCancelled(self):
        """Ensure we cancel notifications that are no longer valid"""
        self.patch.save()
        oldstate = self.patch.state
        state = State.objects.exclude(pk = oldstate.pk)[0]

        self.patch.state = state
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)

        self.patch.state = oldstate
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def testNotificationUpdated(self):
        """Ensure we update notifications when the patch has a second change,
           but keep the original patch details"""
        self.patch.save()
        oldstate = self.patch.state
        newstates = State.objects.exclude(pk = oldstate.pk)[:2]

        self.patch.state = newstates[0]
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.orig_state, oldstate)
        orig_timestamp = notification.last_modified
                         
        self.patch.state = newstates[1]
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.orig_state, oldstate)
        self.assertTrue(notification.last_modified > orig_timestamp)

    def testProjectNotificationsDisabled(self):
        """Ensure we don't see notifications created when a project is
           configured not to send them"""
        self.project.send_notifications = False
        self.project.save()

        self.patch.save()
        oldstate = self.patch.state
        state = State.objects.exclude(pk = oldstate.pk)[0]

        self.patch.state = state
        self.patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

