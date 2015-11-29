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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.models import EmailConfirmation, Person


def _confirmation_url(conf):
    return reverse('patchwork.views.confirm', kwargs = {'key': conf.key})

class TestUser(object):
    username = 'testuser'
    email = 'test@example.com'
    secondary_email = 'test2@example.com'
    password = None

    def __init__(self):
        self.password = User.objects.make_random_password()
        self.user = User.objects.create_user(self.username,
                            self.email, self.password)

class InvalidConfirmationTest(TestCase):
    def setUp(self):
        EmailConfirmation.objects.all().delete()
        Person.objects.all().delete()
        self.user = TestUser()
        self.conf = EmailConfirmation(type = 'userperson',
                                      email = self.user.secondary_email,
                                      user = self.user.user)
        self.conf.save()

    def testInactiveConfirmation(self):
        self.conf.active = False
        self.conf.save()
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/confirm-error.html')
        self.assertEqual(response.context['error'], 'inactive')
        self.assertEqual(response.context['conf'], self.conf)

    def testExpiredConfirmation(self):
        self.conf.date -= self.conf.validity
        self.conf.save()
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/confirm-error.html')
        self.assertEqual(response.context['error'], 'expired')
        self.assertEqual(response.context['conf'], self.conf)

