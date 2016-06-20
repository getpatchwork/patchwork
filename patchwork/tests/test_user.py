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
from django.test import TestCase

from patchwork.models import EmailConfirmation
from patchwork.models import Person
from patchwork.models import UserProfile
from patchwork.tests.utils import create_bundle
from patchwork.tests.utils import create_user
from patchwork.tests.utils import error_strings
from patchwork.tests import utils


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


class UserPersonRequestTest(_UserTestCase):

    def setUp(self):
        super(UserPersonRequestTest, self).setUp()
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


class UserPersonConfirmTest(TestCase):

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


class UserLoginRedirectTest(TestCase):

    def test_user_login_redirect(self):
        url = reverse('user-profile')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('auth_login') + '?next=' + url)


class UserProfileTest(_UserTestCase):

    fixtures = ['default_states']

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


class UserPasswordChangeTest(_UserTestCase):

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
