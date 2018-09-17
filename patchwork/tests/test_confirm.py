# Patchwork - automated patch tracking system
# Copyright (C) 2011 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.models import EmailConfirmation
from patchwork.tests.utils import create_user


def _confirmation_url(conf):
    return reverse('confirm', kwargs={'key': conf.key})


def _generate_secondary_email(user):
    return 'secondary_%d@example.com' % user.id


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
