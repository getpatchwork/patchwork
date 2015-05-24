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

import datetime
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings
from django.db.utils import IntegrityError
from patchwork.models import Patch, State, PatchChangeNotification, EmailOptout
from patchwork.tests.utils import defaults, create_maintainer
from patchwork.utils import send_notifications

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
        self.assertTrue(notification.last_modified >= orig_timestamp)

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

class PatchNotificationEmailTest(TestCase):

    def setUp(self):
        self.project = defaults.project
        self.project.send_notifications = True
        self.project.save()
        self.submitter = defaults.patch_author_person
        self.submitter.save()
        self.patch = Patch(project = self.project, msgid = 'testpatch',
                        name = 'testpatch', content = '',
                        submitter = self.submitter)
        self.patch.save()

    def tearDown(self):
        self.patch.delete()
        self.submitter.delete()
        self.project.delete()

    def _expireNotifications(self, **kwargs):
        timestamp = datetime.datetime.now() - \
                    datetime.timedelta(minutes =
                            settings.NOTIFICATION_DELAY_MINUTES + 1)

        qs = PatchChangeNotification.objects.all()
        if kwargs:
            qs = qs.filter(**kwargs)

        qs.update(last_modified = timestamp)

    def testNoNotifications(self):
        self.assertEquals(send_notifications(), [])

    def testNoReadyNotifications(self):
        """ We shouldn't see immediate notifications"""
        PatchChangeNotification(patch = self.patch,
                               orig_state = self.patch.state).save()

        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 0)

    def testNotifications(self):
        PatchChangeNotification(patch = self.patch,
                               orig_state = self.patch.state).save()
        self._expireNotifications()

        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEquals(msg.to, [self.submitter.email])
        self.assertTrue(self.patch.get_absolute_url() in msg.body)

    def testNotificationEscaping(self):
        self.patch.name = 'Patch name with " character'
        self.patch.save()
        PatchChangeNotification(patch = self.patch,
                               orig_state = self.patch.state).save()
        self._expireNotifications()

        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEquals(msg.to, [self.submitter.email])
        self.assertFalse('&quot;' in msg.body)

    def testNotificationOptout(self):
        """ensure opt-out addresses don't get notifications"""
        PatchChangeNotification(patch = self.patch,
                               orig_state = self.patch.state).save()
        self._expireNotifications()

        EmailOptout(email = self.submitter.email).save()

        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 0)

    def testNotificationMerge(self):
        patches = [self.patch,
                   Patch(project = self.project, msgid = 'testpatch-2',
                         name = 'testpatch 2', content = '',
                         submitter = self.submitter)]

        for patch in patches:
            patch.save()
            PatchChangeNotification(patch = patch,
                                   orig_state = patch.state).save()

        self.assertEquals(PatchChangeNotification.objects.count(), len(patches))
        self._expireNotifications()
        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertTrue(patches[0].get_absolute_url() in msg.body)
        self.assertTrue(patches[1].get_absolute_url() in msg.body)

    def testUnexpiredNotificationMerge(self):
        """Test that when there are multiple pending notifications, with
           at least one within the notification delay, that other notifications
           are held"""
        patches = [self.patch,
                   Patch(project = self.project, msgid = 'testpatch-2',
                         name = 'testpatch 2', content = '',
                         submitter = self.submitter)]

        for patch in patches:
            patch.save()
            PatchChangeNotification(patch = patch,
                                   orig_state = patch.state).save()

        self.assertEquals(PatchChangeNotification.objects.count(), len(patches))
        self._expireNotifications()

        # update one notification, to bring it out of the notification delay
        patches[0].state = State.objects.exclude(pk = patches[0].state.pk)[0]
        patches[0].save()

        # the updated notification should prevent the other from being sent
        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 0)

        # expire the updated notification
        self._expireNotifications()

        errors = send_notifications()
        self.assertEquals(errors, [])
        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertTrue(patches[0].get_absolute_url() in msg.body)
        self.assertTrue(patches[1].get_absolute_url() in msg.body)
