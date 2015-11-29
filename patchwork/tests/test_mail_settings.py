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

import re

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.models import EmailOptout, EmailConfirmation, Person
from patchwork.tests.utils import create_user, error_strings


class MailSettingsTest(TestCase):

    def setUp(self):
        self.url = reverse('patchwork.views.mail.settings')

    def testMailSettingsGET(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'])

    def testMailSettingsPOST(self):
        email = u'foo@example.com'
        response = self.client.post(self.url, {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['email'], email)

    def testMailSettingsPOSTEmpty(self):
        response = self.client.post(self.url, {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-form.html')
        self.assertFormError(response, 'form', 'email',
                'This field is required.')

    def testMailSettingsPOSTInvalid(self):
        response = self.client.post(self.url, {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-form.html')
        self.assertFormError(response, 'form', 'email', error_strings['email'])

    def testMailSettingsPOSTOptedIn(self):
        email = u'foo@example.com'
        response = self.client.post(self.url, {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['is_optout'], False)
        self.assertContains(response, '<strong>may</strong>')
        optout_url = reverse('patchwork.views.mail.optout')
        self.assertContains(response, ('action="%s"' % optout_url))

    def testMailSettingsPOSTOptedOut(self):
        email = u'foo@example.com'
        EmailOptout(email = email).save()
        response = self.client.post(self.url, {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/mail-settings.html')
        self.assertEqual(response.context['is_optout'], True)
        self.assertContains(response, '<strong>may not</strong>')
        optin_url = reverse('patchwork.views.mail.optin')
        self.assertContains(response, ('action="%s"' % optin_url))

class OptoutRequestTest(TestCase):

    def setUp(self):
        self.url = reverse('patchwork.views.mail.optout')

    def testOptOutRequestGET(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('patchwork.views.mail.settings'))

    def testOptoutRequestValidPOST(self):
        email = u'foo@example.com'
        response = self.client.post(self.url, {'email': email})

        # check for a confirmation object
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.get(email = email)

        # check confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['confirmation'], conf)
        self.assertContains(response, email)

        # check email
        url = reverse('patchwork.views.confirm', kwargs = {'key': conf.key})
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [email])
        self.assertEqual(msg.subject, 'Patchwork opt-out confirmation')
        self.assertIn(url, msg.body)

    def testOptoutRequestInvalidPOSTEmpty(self):
        response = self.client.post(self.url, {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                'This field is required.')
        self.assertTrue(response.context['error'])
        self.assertNotIn('email_sent', response.context)
        self.assertEqual(len(mail.outbox), 0)

    def testOptoutRequestInvalidPOSTNonEmail(self):
        response = self.client.post(self.url, {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', error_strings['email'])
        self.assertTrue(response.context['error'])
        self.assertNotIn('email_sent', response.context)
        self.assertEqual(len(mail.outbox), 0)

class OptoutTest(TestCase):

    def setUp(self):
        self.url = reverse('patchwork.views.mail.optout')
        self.email = u'foo@example.com'
        self.conf = EmailConfirmation(type = 'optout', email = self.email)
        self.conf.save()

    def testOptoutValidHash(self):
        url = reverse('patchwork.views.confirm',
                        kwargs = {'key': self.conf.key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/optout.html')
        self.assertContains(response, self.email)

        # check that we've got an optout in the list
        self.assertEqual(EmailOptout.objects.count(), 1)
        self.assertEqual(EmailOptout.objects.all()[0].email, self.email)

        # check that the confirmation is now inactive
        self.assertFalse(EmailConfirmation.objects.get(
                                    pk = self.conf.pk).active)


class OptoutPreexistingTest(OptoutTest):
    """Test that a duplicated opt-out behaves the same as the initial one"""
    def setUp(self):
        super(OptoutPreexistingTest, self).setUp()
        EmailOptout(email = self.email).save()

class OptinRequestTest(TestCase):

    def setUp(self):
        self.url = reverse('patchwork.views.mail.optin')
        self.email = u'foo@example.com'
        EmailOptout(email = self.email).save()

    def testOptInRequestGET(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('patchwork.views.mail.settings'))

    def testOptInRequestValidPOST(self):
        response = self.client.post(self.url, {'email': self.email})

        # check for a confirmation object
        self.assertEqual(EmailConfirmation.objects.count(), 1)
        conf = EmailConfirmation.objects.get(email = self.email)

        # check confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['confirmation'], conf)
        self.assertContains(response, self.email)

        # check email
        url = reverse('patchwork.views.confirm', kwargs = {'key': conf.key})
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [self.email])
        self.assertEqual(msg.subject, 'Patchwork opt-in confirmation')
        self.assertIn(url, msg.body)

    def testOptoutRequestInvalidPOSTEmpty(self):
        response = self.client.post(self.url, {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                'This field is required.')
        self.assertTrue(response.context['error'])
        self.assertNotIn('email_sent', response.context)
        self.assertEqual(len(mail.outbox), 0)

    def testOptoutRequestInvalidPOSTNonEmail(self):
        response = self.client.post(self.url, {'email': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', error_strings['email'])
        self.assertTrue(response.context['error'])
        self.assertNotIn('email_sent', response.context)
        self.assertEqual(len(mail.outbox), 0)

class OptinTest(TestCase):

    def setUp(self):
        self.email = u'foo@example.com'
        self.optout = EmailOptout(email = self.email)
        self.optout.save()
        self.conf = EmailConfirmation(type = 'optin', email = self.email)
        self.conf.save()

    def testOptinValidHash(self):
        url = reverse('patchwork.views.confirm',
                        kwargs = {'key': self.conf.key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patchwork/optin.html')
        self.assertContains(response, self.email)

        # check that there's no optout remaining
        self.assertEqual(EmailOptout.objects.count(), 0)

        # check that the confirmation is now inactive
        self.assertFalse(EmailConfirmation.objects.get(
                                    pk = self.conf.pk).active)

class OptinWithoutOptoutTest(TestCase):
    """Test an opt-in with no existing opt-out"""

    def setUp(self):
        self.url = reverse('patchwork.views.mail.optin')

    def testOptInWithoutOptout(self):
        email = u'foo@example.com'
        response = self.client.post(self.url, {'email': email})

        # check for an error message
        self.assertEqual(response.status_code, 200)
        self.assertTrue(bool(response.context['error']))
        self.assertContains(response, 'not on the patchwork opt-out list')

class UserProfileOptoutFormTest(TestCase):
    """Test that the correct optin/optout forms appear on the user profile
       page, for logged-in users"""

    def setUp(self):
        self.url = reverse('patchwork.views.user.profile')
        self.optout_url = reverse('patchwork.views.mail.optout')
        self.optin_url = reverse('patchwork.views.mail.optin')
        self.form_re_template = ('<form\s+[^>]*action="%(url)s"[^>]*>'
                                 '.*?<input\s+[^>]*value="%(email)s"[^>]*>.*?'
                                 '</form>')
        self.secondary_email = 'test2@example.com'

        self.user = create_user()
        self.client.login(username = self.user.username,
                password = self.user.username)

    def _form_re(self, url, email):
        return re.compile(self.form_re_template % {'url': url, 'email': email},
                          re.DOTALL)

    def testMainEmailOptoutForm(self):
        form_re = self._form_re(self.optout_url, self.user.email)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form_re.search(response.content.decode()) is not None)

    def testMainEmailOptinForm(self):
        EmailOptout(email = self.user.email).save()
        form_re = self._form_re(self.optin_url, self.user.email)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form_re.search(response.content.decode()) is not None)

    def testSecondaryEmailOptoutForm(self):
        p = Person(email = self.secondary_email, user = self.user)
        p.save()
        form_re = self._form_re(self.optout_url, p.email)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form_re.search(response.content.decode()) is not None)

    def testSecondaryEmailOptinForm(self):
        p = Person(email = self.secondary_email, user = self.user)
        p.save()
        EmailOptout(email = p.email).save()

        form_re = self._form_re(self.optin_url, p.email)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form_re.search(response.content.decode()) is not None)
