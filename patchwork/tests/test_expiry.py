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

from patchwork.models import EmailConfirmation, Person, Patch
from patchwork.tests.utils import create_user, defaults
from patchwork.utils import do_expiry


class TestRegistrationExpiry(TestCase):
    fixtures = ['default_states']

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

    def testOldRegistrationExpiry(self):
        date = ((datetime.datetime.now() - EmailConfirmation.validity) -
                datetime.timedelta(hours=1))
        (user, conf) = self.register(date)

        do_expiry()

        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(EmailConfirmation.objects.filter(pk=conf.pk)
                         .exists())

    def testRecentRegistrationExpiry(self):
        date = ((datetime.datetime.now() - EmailConfirmation.validity) +
                datetime.timedelta(hours=1))
        (user, conf) = self.register(date)

        do_expiry()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(EmailConfirmation.objects.filter(pk=conf.pk)
                        .exists())

    def testInactiveRegistrationExpiry(self):
        (user, conf) = self.register(datetime.datetime.now())

        # confirm registration
        conf.user.is_active = True
        conf.user.save()
        conf.deactivate()

        do_expiry()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(EmailConfirmation.objects.filter(pk=conf.pk)
                         .exists())

    def testPatchSubmitterExpiry(self):
        defaults.project.save()
        defaults.patch_author_person.save()

        # someone submits a patch...
        patch = Patch(project=defaults.project,
                      msgid='test@example.com', name='test patch',
                      submitter=defaults.patch_author_person,
                      content=defaults.patch)
        patch.save()

        # ... then starts registration...
        date = ((datetime.datetime.now() - EmailConfirmation.validity) -
                datetime.timedelta(hours=1))
        userid = 'test-user'
        user = User.objects.create_user(
            userid,
            defaults.patch_author_person.email, userid)
        user.is_active = False
        user.date_joined = user.last_login = date
        user.save()

        self.assertEqual(user.email, patch.submitter.email)

        conf = EmailConfirmation(type='registration', user=user,
                                 email=user.email)
        conf.date = date
        conf.save()

        # ... which expires
        do_expiry()

        # we should see no matching user
        self.assertFalse(User.objects.filter(email=patch.submitter.email)
                         .exists())
        # but the patch and person should still be present
        self.assertTrue(Person.objects.filter(
            pk=defaults.patch_author_person.pk).exists())
        self.assertTrue(Patch.objects.filter(pk=patch.pk).exists())

        # and there should be no user associated with the person
        self.assertEqual(
            Person.objects.get(pk=defaults.patch_author_person.pk).user, None)
