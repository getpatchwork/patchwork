# Patchwork - automated patch tracking system
# Copyright (C) 2011 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime

from django.conf import settings
from django.core import mail
from django.test import TestCase

from patchwork.models import EmailOptout
from patchwork.models import PatchChangeNotification
from patchwork.notifications import send_notifications
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state


class PatchNotificationModelTest(TestCase):

    """Tests for the creation and update of the PatchChangeNotifications."""

    def setUp(self):
        self.project = create_project(send_notifications=True)

    def test_patch_creation(self):
        """Ensure we don't get a notification on create."""
        create_patch(project=self.project)
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def test_patch_uninteresting_change(self):
        """Ensure we don't get a notification for "uninteresting" changes"""
        patch = create_patch(project=self.project)

        patch.archived = True
        patch.save()

        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def test_patch_change(self):
        """Ensure we get a notification for interesting patch changes"""
        patch = create_patch(project=self.project)
        oldstate = patch.state
        state = create_state()

        patch.state = state
        patch.save()

        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.patch, patch)
        self.assertEqual(notification.orig_state, oldstate)

    def test_notification_cancelled(self):
        """Ensure we cancel notifications that are no longer valid"""
        patch = create_patch(project=self.project)
        oldstate = patch.state
        state = create_state()

        patch.state = state
        patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)

        patch.state = oldstate
        patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)

    def test_notification_updated(self):
        """Ensure we update notifications when the patch has a second change,
           but keep the original patch details"""
        patch = create_patch(project=self.project)
        oldstate = patch.state
        newstates = [create_state(), create_state()]

        patch.state = newstates[0]
        patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.orig_state, oldstate)

        orig_timestamp = notification.last_modified

        patch.state = newstates[1]
        patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 1)
        notification = PatchChangeNotification.objects.all()[0]
        self.assertEqual(notification.orig_state, oldstate)
        self.assertTrue(notification.last_modified >= orig_timestamp)

    def test_notifications_disabled(self):
        """Ensure we don't see notifications created when a project is
           configured not to send them"""
        patch = create_patch()  # don't use self.project
        state = create_state()

        patch.state = state
        patch.save()
        self.assertEqual(PatchChangeNotification.objects.count(), 0)


class PatchNotificationEmailTest(TestCase):

    def setUp(self):
        self.project = create_project(send_notifications=True)

    def _expire_notifications(self, **kwargs):
        timestamp = datetime.datetime.utcnow() - \
            datetime.timedelta(minutes=settings.NOTIFICATION_DELAY_MINUTES + 1)

        qs = PatchChangeNotification.objects.all()
        if kwargs:
            qs = qs.filter(**kwargs)

        qs.update(last_modified=timestamp)

    def test_no_notifications(self):
        self.assertEqual(send_notifications(), [])

    def test_no_ready_notifications(self):
        """We shouldn't see immediate notifications."""
        patch = create_patch(project=self.project)
        PatchChangeNotification(patch=patch, orig_state=patch.state).save()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 0)

    def test_notifications(self):
        patch = create_patch(project=self.project)
        PatchChangeNotification(patch=patch, orig_state=patch.state).save()

        self._expire_notifications()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [patch.submitter.email])
        self.assertIn(patch.get_absolute_url(), msg.body)

    def test_notification_escaping(self):
        patch = create_patch(name='Patch name with " character',
                             project=self.project)
        PatchChangeNotification(patch=patch, orig_state=patch.state).save()

        self._expire_notifications()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [patch.submitter.email])
        self.assertNotIn('&quot;', msg.body)

    def test_notification_optout(self):
        """Ensure opt-out addresses don't get notifications."""
        patch = create_patch(project=self.project)
        PatchChangeNotification(patch=patch,
                                orig_state=patch.state).save()

        self._expire_notifications()

        EmailOptout(email=patch.submitter.email).save()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 0)

    def test_notification_merge(self):
        """Ensure only one summary email is delivered to each user."""
        patches = create_patches(2, project=self.project)
        for patch in patches:
            PatchChangeNotification(patch=patch, orig_state=patch.state).save()

        self.assertEqual(PatchChangeNotification.objects.count(), len(patches))
        self._expire_notifications()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        for patch in patches:
            self.assertIn(patch.get_absolute_url(), msg.body)

    def test_unexpired_notification_merge(self):
        """Test that when there are multiple pending notifications, with
           at least one within the notification delay, that other notifications
           are held"""
        patches = create_patches(2, project=self.project)
        for patch in patches:
            patch.save()
            PatchChangeNotification(patch=patch, orig_state=patch.state).save()

        state = create_state()

        self.assertEqual(PatchChangeNotification.objects.count(), len(patches))
        self._expire_notifications()

        # update one notification, to bring it out of the notification delay

        patches[0].state = state
        patches[0].save()

        # the updated notification should prevent the other from being sent
        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 0)

        # expire the updated notification
        self._expire_notifications()

        errors = send_notifications()
        self.assertEqual(errors, [])
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        for patch in patches:
            self.assertIn(patch.get_absolute_url(), msg.body)
