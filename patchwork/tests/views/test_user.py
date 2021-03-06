# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.auth.models import User
from django.core import mail
from django.test.client import Client
from django.test import TestCase
from django.urls import reverse

from patchwork.models import EmailConfirmation
from patchwork.models import Person
from patchwork.models import UserProfile
from patchwork.tests import utils
from patchwork.tests.utils import create_bundle
from patchwork.tests.utils import create_user
from patchwork.tests.utils import error_strings


def _confirmation_url(conf):
    return reverse('confirm', kwargs={'key': conf.key})


def _generate_secondary_email(user):
    return 'secondary_%d@example.com' % user.id


class _UserTestCase(TestCase):

    def setUp(self):
        self.user = create_user()
        self.password = User.objects.make_random_password()
        self.user.set_password(self.password)
        self.user.save()

        self.client.login(username=self.user.username,
                          password=self.password)


class TestUser(object):
    firstname = 'Test'
    lastname = 'User'
    fullname = ' '.join([firstname, lastname])
    username = 'testuser'
    email = 'test@example.com'
    password = 'foobar'


class RegistrationTest(TestCase):

    def setUp(self):
        self.user = TestUser()
        self.client = Client()
        self.default_data = {
            'username': self.user.username,
            'first_name': self.user.firstname,
            'last_name': self.user.lastname,
            'email': self.user.email,
            'password': self.user.password,
        }
        self.required_error = 'This field is required.'
        self.invalid_error = 'Enter a valid value.'

    def test_registration_form(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/registration.html')

    def test_blank_fields(self):
        for field in ['username', 'email', 'password']:
            data = self.default_data.copy()
            del data[field]
            response = self.client.post('/register/', data)
            self.assertEqual(response.status_code, 200)
            self.assertFormError(response, 'form', field, self.required_error)

    def test_invalid_username(self):
        data = self.default_data.copy()
        data['username'] = 'invalid user'
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', self.invalid_error)

    def test_existing_username(self):
        user = create_user()
        data = self.default_data.copy()
        data['username'] = user.username
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'username',
            'This username is already taken. Please choose another.')

    def test_existing_email(self):
        user = create_user()
        data = self.default_data.copy()
        data['email'] = user.email
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'email',
            'This email address is already in use for the account '
            '"%s".\n' % user.username)

    def test_valid_registration(self):
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
        confs = EmailConfirmation.objects.filter(
            user=user, type='registration')
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
        self.default_data = {
            'username': self.user.username,
            'first_name': self.user.firstname,
            'last_name': self.user.lastname,
            'email': self.user.email,
            'password': self.user.password
        }

    def test_valid(self):
        """Test the success path."""
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

    def test_new_person_setup(self):
        """Ensure a new Person is created after account setup.

        Create an account for a never before seen email. Check that a Person
        object is created after registration and has the correct details.
        """
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

        self.assertEqual(person.name, self.user.fullname)

    def test_existing_person_setup(self):
        """Ensure an existing person is linked after account setup.

        Create an account for a user using an email we've previously seen.
        Check that the person object is updated after registration with the
        correct details.
        """
        person = Person(name=self.user.fullname, email=self.user.email)
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

        self.assertEqual(person.name, self.user.fullname)

    def test_existing_person_unmodified(self):
        """Ensure an existing person is not linked until registration is done.

        Create an account for a user using an email we've previously seen but
        don't confirm it. Check that the person object is not updated yet.
        """
        person = Person(name=self.user.fullname, email=self.user.email)
        person.save()

        # register
        data = self.default_data.copy()
        data['first_name'] = 'invalid'
        data['last_name'] = 'invalid'
        self.assertEqual(data['email'], person.email)
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            Person.objects.get(pk=person.pk).name, self.user.fullname)


class UserLinkTest(_UserTestCase):

    def setUp(self):
        super().setUp()
        self.secondary_email = _generate_secondary_email(self.user)

    def test_user_person_request_form(self):
        response = self.client.get(reverse('user-link'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['linkform'])

    def test_user_person_request_empty(self):
        response = self.client.post(reverse('user-link'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['linkform'])
        self.assertFormError(response, 'linkform', 'email',
                             'This field is required.')

    def test_user_person_request_invalid(self):
        response = self.client.post(reverse('user-link'), {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['linkform'])
        self.assertFormError(response, 'linkform', 'email',
                             error_strings['email'])

    def test_user_person_request_valid(self):
        response = self.client.post(reverse('user-link'),
                                    {'email': self.secondary_email})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['confirmation'])

        # check that we have a confirmation saved
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.all()[0]
        self.assertEqual(conf.user, self.user)
        self.assertEqual(conf.email, self.secondary_email)
        self.assertEqual(conf.type, 'userperson')

        # check that an email has gone out...
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, 'Patchwork email address confirmation')
        self.assertIn(self.secondary_email, msg.to)
        self.assertIn(_confirmation_url(conf), msg.body)

        # ...and that the URL is valid
        response = self.client.get(_confirmation_url(conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/user-link-confirm.html')


class ConfirmationTest(TestCase):

    def setUp(self):
        self.user = create_user(link_person=False)
        self.password = User.objects.make_random_password()
        self.user.set_password(self.password)
        self.user.save()

        self.client.login(username=self.user.username,
                          password=self.password)

        self.secondary_email = _generate_secondary_email(self.user)
        self.conf = EmailConfirmation(type='userperson',
                                      email=self.secondary_email,
                                      user=self.user)
        self.conf.save()

    def test_user_person_confirm(self):
        self.assertEqual(Person.objects.count(), 0)
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEqual(response.status_code, 200)

        # check that the Person object has been created and linked
        self.assertEqual(Person.objects.count(), 1)
        person = Person.objects.get(email=self.secondary_email)
        self.assertEqual(person.email, self.secondary_email)
        self.assertEqual(person.user, self.user)

        # check that the confirmation has been marked as inactive. We
        # need to reload the confirmation to check this.
        conf = EmailConfirmation.objects.get(pk=self.conf.pk)
        self.assertEqual(conf.active, False)


class InvalidConfirmationTest(TestCase):

    def setUp(self):
        self.user = create_user()
        self.secondary_email = _generate_secondary_email(self.user)

        self.conf = EmailConfirmation(type='userperson',
                                      email=self.secondary_email,
                                      user=self.user)
        self.conf.save()

    def test_inactive_confirmation(self):
        self.conf.active = False
        self.conf.save()
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/confirm-error.html')
        self.assertEqual(response.context['error'], 'inactive')
        self.assertEqual(response.context['conf'], self.conf)

    def test_expired_confirmation(self):
        self.conf.date -= self.conf.validity
        self.conf.save()
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/confirm-error.html')
        self.assertEqual(response.context['error'], 'expired')
        self.assertEqual(response.context['conf'], self.conf)


class LoginRedirectTest(TestCase):

    def test_user_login_redirect(self):
        url = reverse('user-profile')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('auth_login') + '?next=' + url)


class UserProfileTest(_UserTestCase):

    def test_user_profile(self):
        response = self.client.get(reverse('user-profile'))
        self.assertContains(response, 'Your Profile')
        self.assertContains(response, 'You have no bundles')

    def test_user_profile_bundles(self):
        bundle = create_bundle(owner=self.user)

        response = self.client.get(reverse('user-profile'))

        self.assertContains(response, 'Your Profile')
        self.assertContains(response, 'You have the following bundle')
        self.assertContains(response, bundle.get_absolute_url())

    def test_user_profile_todos(self):
        patches = utils.create_patches(5)
        for patch in patches:
            patch.delegate = self.user
            patch.save()

        response = self.client.get(reverse('user-profile'))

        self.assertContains(response, 'contains 5')
        self.assertContains(response, reverse('user-todos'))

    def test_user_profile_valid_post(self):
        user_profile = UserProfile.objects.get(user=self.user.id)
        old_ppp = user_profile.items_per_page
        new_ppp = old_ppp + 1

        self.client.post(reverse('user-profile'), {'items_per_page': new_ppp})

        user_profile = UserProfile.objects.get(user=self.user.id)
        self.assertEqual(user_profile.items_per_page, new_ppp)

    def test_user_profile_invalid_post(self):
        user_profile = UserProfile.objects.get(user=self.user.id)
        old_ppp = user_profile.items_per_page
        new_ppp = -1

        self.client.post(reverse('user-profile'), {'items_per_page': new_ppp})

        user_profile = UserProfile.objects.get(user=self.user.id)
        self.assertEqual(user_profile.items_per_page, old_ppp)


class PasswordChangeTest(_UserTestCase):

    def test_password_change_form(self):
        response = self.client.get(reverse('password_change'))
        self.assertContains(response, 'Change my password')

    def test_password_change(self):
        old_password = self.password
        new_password = User.objects.make_random_password()

        data = {
            'old_password': old_password,
            'new_password1': new_password,
            'new_password2': new_password,
        }

        response = self.client.post(reverse('password_change'), data)
        self.assertRedirects(response, reverse('password_change_done'))

        user = User.objects.get(id=self.user.id)

        self.assertFalse(user.check_password(old_password))
        self.assertTrue(user.check_password(new_password))

        response = self.client.get(reverse('password_change_done'))
        self.assertContains(response,
                            "Your password has been changed successfully")


class UserUnlinkTest(_UserTestCase):

    def _create_confirmation(self, email):
        conf = EmailConfirmation(type='userperson',
                                 email=email,
                                 user=self.user)
        conf.save()
        self.client.get(_confirmation_url(conf))

    def _test_unlink_post(self, email, expect_none=False):
        self._create_confirmation(email)

        person = Person.objects.get(email=email)
        response = self.client.post(reverse('user-unlink', args=[person.id]))
        self.assertRedirects(response, reverse('user-profile'))

    def test_unlink_primary_email(self):
        self._test_unlink_post(self.user.email)

        person = Person.objects.get(email=self.user.email)
        self.assertEqual(person.user, self.user)

    def test_unlink_secondary_email(self):
        secondary_email = _generate_secondary_email(self.user)

        self._test_unlink_post(secondary_email)

        person = Person.objects.get(email=secondary_email)
        self.assertIsNone(person.user)

    def test_unlink_another_user(self):
        other_user = create_user()

        self._test_unlink_post(other_user.email)

        person = Person.objects.get(email=other_user.email)
        self.assertIsNone(person.user)

    def test_unlink_non_post(self):
        secondary_email = _generate_secondary_email(self.user)

        self._create_confirmation(secondary_email)

        person = Person.objects.get(email=secondary_email)
        response = self.client.get(reverse('user-unlink', args=[person.id]))
        self.assertRedirects(response, reverse('user-profile'))

        person = Person.objects.get(email=secondary_email)
        self.assertEqual(person.user, self.user)
