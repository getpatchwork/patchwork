# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from patchwork.models import EmailOptout
from patchwork.models import EmailConfirmation
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_user
from patchwork.tests.utils import error_strings


class MailSettingsTest(TestCase):

    def test_get(self):
        response = self.client.get(reverse('mail-settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'])

    def test_post(self):
        email = u'foo@example.com'
        response = self.client.post(reverse('mail-settings'), {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['email'], email)

    def test_post_empty(self):
        response = self.client.post(reverse('mail-settings'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail.html')
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')

    def test_post_invalid(self):
        response = self.client.post(reverse('mail-settings'), {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail.html')
        self.assertFormError(response, 'form', 'email', error_strings['email'])

    def test_post_optin(self):
        email = u'foo@example.com'
        response = self.client.post(reverse('mail-settings'), {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['is_optout'], False)
        self.assertContains(response, '<strong>may</strong>')
        self.assertContains(response, 'action="%s"' % reverse('mail-optout'))

    def test_post_optout(self):
        email = u'foo@example.com'
        EmailOptout(email=email).save()
        response = self.client.post(reverse('mail-settings'), {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['is_optout'], True)
        self.assertContains(response, '<strong>may not</strong>')
        self.assertContains(response, 'action="%s"' % reverse('mail-optin'))


class OptoutRequestTest(TestCase):

    def test_get(self):
        response = self.client.get(reverse('mail-optout'))
        self.assertRedirects(response, reverse('mail-settings'))

    def test_post(self):
        email = u'foo@example.com'
        response = self.client.post(reverse('mail-optout'), {'email': email})

        # check for a confirmation object
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.get(email=email)

        # check confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['confirmation'], conf)
        self.assertContains(response, email)

        # check email
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [email])
        self.assertEqual(msg.subject, 'Patchwork opt-out request')
        self.assertIn(reverse('confirm', kwargs={'key': conf.key}), msg.body)

    def test_post_empty(self):
        response = self.client.post(reverse('mail-optout'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertTrue(response.context['error'])
        self.assertNotIn('confirmation', response.context)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_non_email(self):
        response = self.client.post(reverse('mail-optout'), {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', error_strings['email'])
        self.assertTrue(response.context['error'])
        self.assertNotIn('confirmation', response.context)
        self.assertEqual(len(mail.outbox), 0)


class OptoutTest(TestCase):

    def setUp(self):
        self.email = u'foo@example.com'
        self.conf = EmailConfirmation(type='optout', email=self.email)
        self.conf.save()

    def test_valid_hash(self):
        url = reverse('confirm', kwargs={'key': self.conf.key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/optout.html')
        self.assertContains(response, self.email)

        # check that we've got an optout in the list
        self.assertEqual(EmailOptout.objects.count(), 1)
        self.assertEqual(EmailOptout.objects.all()[0].email, self.email)

        # check that the confirmation is now inactive
        self.assertFalse(EmailConfirmation.objects.get(
            pk=self.conf.pk).active)


class OptoutPreexistingTest(OptoutTest):

    """Test that a duplicated opt-out behaves the same as the initial one"""

    def setUp(self):
        super(OptoutPreexistingTest, self).setUp()
        EmailOptout(email=self.email).save()


class OptinRequestTest(TestCase):
    email = u'foo@example.com'

    def setUp(self):
        EmailOptout(email=self.email).save()

    def test_get(self):
        response = self.client.get(reverse('mail-optin'))
        self.assertRedirects(response, reverse('mail-settings'))

    def test_post(self):
        response = self.client.post(reverse('mail-optin'),
                                    {'email': self.email})

        # check for a confirmation object
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.get(email=self.email)

        # check confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['confirmation'], conf)
        self.assertContains(response, self.email)

        # check email
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [self.email])
        self.assertEqual(msg.subject, 'Patchwork opt-in request')
        self.assertIn(reverse('confirm', kwargs={'key': conf.key}), msg.body)

    def test_post_empty(self):
        response = self.client.post(reverse('mail-optin'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        self.assertTrue(response.context['error'])
        self.assertNotIn('confirmation', response.context)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_non_email(self):
        response = self.client.post(reverse('mail-optin'), {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', error_strings['email'])
        self.assertTrue(response.context['error'])
        self.assertNotIn('confirmation', response.context)
        self.assertEqual(len(mail.outbox), 0)


class OptinTest(TestCase):

    def setUp(self):
        self.email = u'foo@example.com'
        self.optout = EmailOptout(email=self.email)
        self.optout.save()
        self.conf = EmailConfirmation(type='optin', email=self.email)
        self.conf.save()

    def test_valid_hash(self):
        response = self.client.get(
            reverse('confirm', kwargs={'key': self.conf.key}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/optin.html')
        self.assertContains(response, self.email)

        # check that there's no optout remaining
        self.assertEqual(EmailOptout.objects.count(), 0)

        # check that the confirmation is now inactive
        self.assertFalse(EmailConfirmation.objects.get(
            pk=self.conf.pk).active)


class OptinWithoutOptoutTest(TestCase):

    """Test an opt-in with no existing opt-out."""

    def test_opt_in_without_optout(self):
        email = u'foo@example.com'
        response = self.client.post(reverse('mail-optin'), {'email': email})

        # check for an error message
        self.assertEqual(response.status_code, 200)
        self.assertTrue(bool(response.context['error']))
        self.assertContains(response, 'not on the patchwork opt-out list')


class UserProfileOptoutFormTest(TestCase):

    """Validate presence of correct optin/optout forms."""

    form_re_template = (r'<form\s+[^>]*action="%(url)s"[^>]*>'
                        r'.*?<input\s+[^>]*value="%(email)s"[^>]*>.*?'
                        r'</form>')

    def setUp(self):
        self.secondary_email = 'test2@example.com'

        self.user = create_user()

        self.client.login(username=self.user.username,
                          password=self.user.username)

    def _form_re(self, url, email):
        return re.compile(self.form_re_template % {'url': url, 'email': email},
                          re.DOTALL)

    def test_primary_email_optout_form(self):
        form_re = self._form_re(reverse('mail-optout'), self.user.email)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(form_re.search(response.content.decode()))

    def test_primary_email_optin_form(self):
        EmailOptout(email=self.user.email).save()
        form_re = self._form_re(reverse('mail-optin'), self.user.email)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(form_re.search(response.content.decode()))

    def test_secondary_email_optout_form(self):
        person = create_person(email=self.secondary_email, user=self.user)
        form_re = self._form_re(reverse('mail-optout'), person.email)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(form_re.search(response.content.decode()))

    def test_secondary_email_optin_form(self):
        person = create_person(email=self.secondary_email, user=self.user)
        EmailOptout(email=person.email).save()
        form_re = self._form_re(reverse('mail-optin'), person.email)
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(form_re.search(response.content.decode()))
