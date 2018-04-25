# Patchwork - automated patch tracking system
# Copyright (C) 2014 Jeremy Kerr <jk@ozlabs.org>
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

from django.contrib.auth.models import User
from django.test import TestCase

from patchwork.models import EmailConfirmation
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.notifications import expire_notifications
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_user


class TestRegistrationExpiry(TestCase):

    def register(self, date):
        user = create_user()
        user.is_active = False
        user.date_joined = user.last_login = date
        user.save()

        conf = EmailConfirmation(type='registration', user=user,
                                 email=user.email)
        conf.date = date
        conf.save()

        return (user, conf)

    def test_old_registration_expiry(self):
        date = ((datetime.datetime.utcnow() - EmailConfirmation.validity) -
                datetime.timedelta(hours=1))
        user, conf = self.register(date)

        expire_notifications()

        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(
            EmailConfirmation.objects.filter(pk=conf.pk).exists())

    def test_recent_registration_expiry(self):
        date = ((datetime.datetime.utcnow() - EmailConfirmation.validity) +
                datetime.timedelta(hours=1))
        user, conf = self.register(date)

        expire_notifications()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(
            EmailConfirmation.objects.filter(pk=conf.pk).exists())

    def test_inactive_registration_expiry(self):
        user, conf = self.register(datetime.datetime.utcnow())

        # confirm registration
        conf.user.is_active = True
        conf.user.save()
        conf.deactivate()

        expire_notifications()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(
            EmailConfirmation.objects.filter(pk=conf.pk).exists())

    def test_patch_submitter_expiry(self):
        # someone submits a patch...
        patch = create_patch()
        submitter = patch.submitter

        # ... then starts registration...
        date = ((datetime.datetime.utcnow() - EmailConfirmation.validity) -
                datetime.timedelta(hours=1))
        user = create_user(link_person=False, email=submitter.email)
        user.is_active = False
        user.date_joined = user.last_login = date
        user.save()

        conf = EmailConfirmation(type='registration', user=user,
                                 email=user.email)
        conf.date = date
        conf.save()

        # ... which expires
        expire_notifications()

        # we should see no matching user
        self.assertFalse(User.objects.filter(email=patch.submitter.email)
                         .exists())
        # but the patch and person should still be present
        self.assertTrue(Person.objects.filter(pk=submitter.pk).exists())
        self.assertTrue(Patch.objects.filter(pk=patch.pk).exists())
        # and there should be no user associated with the person
        self.assertEqual(Person.objects.get(pk=submitter.pk).user, None)
