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

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase

from patchwork.models import EmailConfirmation, Person
from patchwork.tests.utils import create_user


def _confirmation_url(conf):
    return reverse('patchwork.views.confirm', kwargs={'key': conf.key})


class TestUser(object):
    firstname = 'Test'
    lastname = 'User'
    username = 'testuser'
    email = 'test@example.com'
    password = 'foobar'


class RegistrationTest(TestCase):

    def setUp(self):
        self.user = TestUser()
        self.client = Client()
        self.default_data = {'username': self.user.username,
                             'first_name': self.user.firstname,
                             'last_name': self.user.lastname,
                             'email': self.user.email,
                             'password': self.user.password}
        self.required_error = 'This field is required.'
        self.invalid_error = 'Enter a valid value.'

    def testRegistrationForm(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/registration_form.html')

    def testBlankFields(self):
        for field in ['username', 'email', 'password']:
            data = self.default_data.copy()
            del data[field]
            response = self.client.post('/register/', data)
            self.assertEqual(response.status_code, 200)
            self.assertFormError(response, 'form', field, self.required_error)

    def testInvalidUsername(self):
        data = self.default_data.copy()
        data['username'] = 'invalid user'
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', self.invalid_error)

    def testExistingUsername(self):
        user = create_user()
        data = self.default_data.copy()
        data['username'] = user.username
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username',
                             'This username is already taken. Please choose '
                             'another.')

    def testExistingEmail(self):
        user = create_user()
        data = self.default_data.copy()
        data['email'] = user.email
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This email address is already in use '
                             'for the account "%s".\n' % user.username)

    def testValidRegistration(self):
        response = self.client.post('/register/', self.default_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'confirmation email has been sent')

        # check for presence of an inactive user object
        users = User.objects.filter(username=self.user.username)
        self.assertEqual(users.count(), 1)
        user = users[0]
        self.assertEqual(user.username, self.user.username)
        self.assertEqual(user.email, self.user.email)
        self.assertEqual(user.is_active, False)

        # check for confirmation object
        confs = EmailConfirmation.objects.filter(user=user,
                                                 type='registration')
        self.assertEqual(len(confs), 1)
        conf = confs[0]
        self.assertEqual(conf.email, self.user.email)

        # check for a sent mail
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, 'Patchwork account confirmation')
        self.assertIn(self.user.email, msg.to)
        self.assertIn(_confirmation_url(conf), msg.body)

        # ...and that the URL is valid
        response = self.client.get(_confirmation_url(conf))
        self.assertEqual(response.status_code, 200)


class RegistrationConfirmationTest(TestCase):

    def setUp(self):
        self.user = TestUser()
        self.default_data = {'username': self.user.username,
                             'first_name': self.user.firstname,
                             'last_name': self.user.lastname,
                             'email': self.user.email,
                             'password': self.user.password}

    def testRegistrationConfirmation(self):
        self.assertEqual(EmailConfirmation.objects.count(), 0)
        response = self.client.post('/register/', self.default_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'confirmation email has been sent')

        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.filter()[0]
        self.assertFalse(conf.user.is_active)
        self.assertTrue(conf.active)

        response = self.client.get(_confirmation_url(conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'patchwork/registration-confirm.html')

        conf = EmailConfirmation.objects.get(pk=conf.pk)
        self.assertTrue(conf.user.is_active)
        self.assertFalse(conf.active)

    def testRegistrationNewPersonSetup(self):
        """ Check that the person object created after registration has the
            correct details """

        # register
        self.assertEqual(EmailConfirmation.objects.count(), 0)
        response = self.client.post('/register/', self.default_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Person.objects.exists())

        # confirm
        conf = EmailConfirmation.objects.filter()[0]
        response = self.client.get(_confirmation_url(conf))
        self.assertEqual(response.status_code, 200)

        qs = Person.objects.filter(email=self.user.email)
        self.assertTrue(qs.exists())
        person = Person.objects.get(email=self.user.email)

        self.assertEqual(person.name,
                         self.user.firstname + ' ' + self.user.lastname)

    def testRegistrationExistingPersonSetup(self):
        """ Check that the person object created after registration has the
            correct details """

        fullname = self.user.firstname + ' ' + self.user.lastname
        person = Person(name=fullname, email=self.user.email)
        person.save()

        # register
        self.assertEqual(EmailConfirmation.objects.count(), 0)
        response = self.client.post('/register/', self.default_data)
        self.assertEqual(response.status_code, 200)

        # confirm
        conf = EmailConfirmation.objects.filter()[0]
        response = self.client.get(_confirmation_url(conf))
        self.assertEqual(response.status_code, 200)

        person = Person.objects.get(email=self.user.email)

        self.assertEqual(person.name, fullname)

    def testRegistrationExistingPersonUnmodified(self):
        """ Check that an unconfirmed registration can't modify an existing
            Person object"""

        fullname = self.user.firstname + ' ' + self.user.lastname
        person = Person(name=fullname, email=self.user.email)
        person.save()

        # register
        data = self.default_data.copy()
        data['first_name'] = 'invalid'
        data['last_name'] = 'invalid'
        self.assertEqual(data['email'], person.email)
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Person.objects.get(pk=person.pk).name, fullname)
