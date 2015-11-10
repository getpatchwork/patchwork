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

from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from patchwork.models import EmailConfirmation, Person, Bundle, UserProfile
from patchwork.tests.utils import defaults, error_strings


def _confirmation_url(conf):
    return reverse('patchwork.views.confirm', kwargs = {'key': conf.key})

class TestUser(object):

    def __init__(self, username='testuser', email='test@example.com',
                 secondary_email='test2@example.com'):
        self.username = username
        self.email = email
        self.secondary_email = secondary_email
        self.password = User.objects.make_random_password()
        self.user = User.objects.create_user(
            self.username, self.email, self.password)


class UserPersonRequestTest(TestCase):
    def setUp(self):
        self.user = TestUser()
        self.client.login(username = self.user.username,
                          password = self.user.password)
        EmailConfirmation.objects.all().delete()

    def testUserPersonRequestForm(self):
        response = self.client.get('/user/link/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.context['linkform'])

    def testUserPersonRequestEmpty(self):
        response = self.client.post('/user/link/', {'email': ''})
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.context['linkform'])
        self.assertFormError(response, 'linkform', 'email',
                'This field is required.')

    def testUserPersonRequestInvalid(self):
        response = self.client.post('/user/link/', {'email': 'foo'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.context['linkform'])
        self.assertFormError(response, 'linkform', 'email',
                                error_strings['email'])

    def testUserPersonRequestValid(self):
        response = self.client.post('/user/link/',
                                {'email': self.user.secondary_email})
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.context['confirmation'])

        # check that we have a confirmation saved
        self.assertEquals(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.all()[0]
        self.assertEquals(conf.user, self.user.user)
        self.assertEquals(conf.email, self.user.secondary_email)
        self.assertEquals(conf.type, 'userperson')

        # check that an email has gone out...
        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEquals(msg.subject, 'Patchwork email address confirmation')
        self.assertTrue(self.user.secondary_email in msg.to)
        self.assertTrue(_confirmation_url(conf) in msg.body)

        # ...and that the URL is valid
        response = self.client.get(_confirmation_url(conf))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/user-link-confirm.html')

class UserPersonConfirmTest(TestCase):
    def setUp(self):
        EmailConfirmation.objects.all().delete()
        Person.objects.all().delete()
        self.user = TestUser()
        self.client.login(username = self.user.username,
                          password = self.user.password)
        self.conf = EmailConfirmation(type = 'userperson',
                                      email = self.user.secondary_email,
                                      user = self.user.user)
        self.conf.save()

    def testUserPersonConfirm(self):
        self.assertEquals(Person.objects.count(), 0)
        response = self.client.get(_confirmation_url(self.conf))
        self.assertEquals(response.status_code, 200)

        # check that the Person object has been created and linked
        self.assertEquals(Person.objects.count(), 1)
        person = Person.objects.get(email = self.user.secondary_email)
        self.assertEquals(person.email, self.user.secondary_email)
        self.assertEquals(person.user, self.user.user)

        # check that the confirmation has been marked as inactive. We
        # need to reload the confirmation to check this.
        conf = EmailConfirmation.objects.get(pk = self.conf.pk)
        self.assertEquals(conf.active, False)

class UserLoginRedirectTest(TestCase):

    def testUserLoginRedirect(self):
        url = '/user/'
        response = self.client.get(url)
        self.assertRedirects(response, settings.LOGIN_URL + '?next=' + url)

class UserProfileTest(TestCase):

    def setUp(self):
        self.user = TestUser()
        self.client.login(username = self.user.username,
                          password = self.user.password)

    def testUserProfile(self):
        response = self.client.get('/user/')
        self.assertContains(response, 'User Profile: %s' % self.user.username)

    def testUserProfileNoBundles(self):
        response = self.client.get('/user/')
        self.assertContains(response, 'You have no bundles')

    def testUserProfileBundles(self):
        project = defaults.project
        project.save()

        bundle = Bundle(project = project, name = 'test-1',
                        owner = self.user.user)
        bundle.save()

        response = self.client.get('/user/')

        self.assertContains(response, 'You have the following bundle')
        self.assertContains(response, bundle.get_absolute_url())

    def testUserProfileValidPost(self):
        user_profile = UserProfile.objects.get(user=self.user.user.id)
        old_ppp = user_profile.patches_per_page
        new_ppp = old_ppp + 1

        response = self.client.post('/user/', {'patches_per_page': new_ppp})

        user_profile = UserProfile.objects.get(user=self.user.user.id)
        self.assertEquals(user_profile.patches_per_page, new_ppp)

    def testUserProfileInvalidPost(self):
        user_profile = UserProfile.objects.get(user=self.user.user.id)
        old_ppp = user_profile.patches_per_page
        new_ppp = -1

        response = self.client.post('/user/', {'patches_per_page': new_ppp})

        user_profile = UserProfile.objects.get(user=self.user.user.id)
        self.assertEquals(user_profile.patches_per_page, old_ppp)


class UserPasswordChangeTest(TestCase):
    user = None

    def setUp(self):
        self.form_url = reverse('django.contrib.auth.views.password_change')
        self.done_url = reverse(
            'django.contrib.auth.views.password_change_done')

    def testPasswordChangeForm(self):
        self.user = TestUser()
        self.client.login(username = self.user.username,
                          password = self.user.password)

        response = self.client.get(self.form_url)
        self.assertContains(response, 'Change my password')

    def testPasswordChange(self):
        self.user = TestUser()
        self.client.login(username = self.user.username,
                          password = self.user.password)

        old_password = self.user.password
        new_password = User.objects.make_random_password()

        data = {
            'old_password': old_password,
            'new_password1': new_password,
            'new_password2': new_password,
        }

        response = self.client.post(self.form_url, data)
        self.assertRedirects(response, self.done_url)

        user = User.objects.get(id = self.user.user.id)

        self.assertFalse(user.check_password(old_password))
        self.assertTrue(user.check_password(new_password))

        response = self.client.get(self.done_url)
        self.assertContains(response,
                "Your password has been changed sucessfully")

class UserUnlinkTest(TestCase):
    def setUp(self):
        self.form_url = '/user/unlink/{pid}/'
        self.done_url = '/user/'
        EmailConfirmation.objects.all().delete()
        Person.objects.all().delete()

    def testUnlinkPrimaryEmail(self):
        user = TestUser()
        self.client.login(username=user.username,
                          password=user.password)
        conf = EmailConfirmation(type='userperson',
                                 email=user.email,
                                 user=user.user)
        conf.save()
        self.client.get(_confirmation_url(conf))

        person = Person.objects.get(email=user.email)
        response = self.client.post(self.form_url.format(pid=str(person.id)))
        self.assertRedirects(response, self.done_url)

        person = Person.objects.get(email=user.email)
        self.assertEquals(person.user, user.user)

    def testUnlinkSecondaryEmail(self):
        user = TestUser()
        self.client.login(username=user.username,
                          password=user.password)
        conf = EmailConfirmation(type='userperson',
                                 email=user.secondary_email,
                                 user=user.user)
        conf.save()
        self.client.get(_confirmation_url(conf))

        person = Person.objects.get(email=user.secondary_email)
        response = self.client.post(self.form_url.format(pid=str(person.id)))
        self.assertRedirects(response, self.done_url)

        person = Person.objects.get(email=user.secondary_email)
        self.assertEquals(person.user, None)

    def testUnlinkAnotherUser(self):
        user = TestUser()
        self.client.login(username=user.username,
                          password=user.password)

        other_user = TestUser('testuser_other', 'test_other@example.com',
                              'test_other2@example.com')
        conf = EmailConfirmation(type='userperson',
                                 email=other_user.email,
                                 user=other_user.user)
        conf.save()
        self.client.get(_confirmation_url(conf))

        person = Person.objects.get(email=other_user.email)
        response = self.client.post(self.form_url.format(pid=str(person.id)))
        self.assertRedirects(response, self.done_url)

        person = Person.objects.get(email=other_user.email)
        self.assertEquals(person.user, None)

    def testUnlinkNonPost(self):
        user = TestUser()
        self.client.login(username=user.username,
                          password=user.password)
        conf = EmailConfirmation(type='userperson',
                                 email=user.secondary_email,
                                 user=user.user)
        conf.save()
        self.client.get(_confirmation_url(conf))

        person = Person.objects.get(email=user.secondary_email)
        response = self.client.get(self.form_url.format(pid=str(person.id)))
        self.assertRedirects(response, self.done_url)

        person = Person.objects.get(email=user.secondary_email)
        self.assertEquals(person.user, user.user)
