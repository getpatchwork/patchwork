# Patchwork - automated patch tracking system
# Copyright (C) 2023 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import configparser

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user


class PwclientrcTest(TestCase):
    def setUp(self):
        super().setUp()
        self.project = create_project()

    def _get_pwclientrc(self):
        response = self.client.get(
            reverse('pwclientrc', kwargs={'project_id': self.project.linkname})
        )

        pwclientrc = configparser.ConfigParser()
        pwclientrc.read_string(response.content.decode())

        return pwclientrc

    @override_settings(ENABLE_REST_API=False)
    def test_xmlrpc(self):
        pwclientrc = self._get_pwclientrc()

        self.assertTrue(pwclientrc.has_section(self.project.linkname))
        self.assertTrue(
            pwclientrc.has_option(self.project.linkname, 'backend')
        )
        self.assertEqual(
            'xmlrpc', pwclientrc.get(self.project.linkname, 'backend')
        )

    @override_settings(ENABLE_REST_API=True)
    def test_rest(self):
        pwclientrc = self._get_pwclientrc()

        self.assertTrue(pwclientrc.has_section(self.project.linkname))
        self.assertTrue(
            pwclientrc.has_option(self.project.linkname, 'backend')
        )
        self.assertEqual(
            'rest', pwclientrc.get(self.project.linkname, 'backend')
        )
        self.assertFalse(pwclientrc.has_option(self.project, 'username'))
        self.assertFalse(pwclientrc.has_option(self.project, 'password'))

    @override_settings(ENABLE_REST_API=True)
    def test_rest_auth(self):
        user = create_user()
        user.set_password('12345')
        user.save()
        self.client.login(
            username=user.username,
            password='12345',
        )

        pwclientrc = self._get_pwclientrc()

        self.assertTrue(pwclientrc.has_section(self.project.linkname))
        self.assertTrue(
            pwclientrc.has_option(self.project.linkname, 'backend')
        )
        self.assertEqual(
            'rest', pwclientrc.get(self.project.linkname, 'backend')
        )
        self.assertTrue(
            pwclientrc.has_option(self.project.linkname, 'username')
        )
        self.assertEqual(
            user.username,
            pwclientrc.get(self.project.linkname, 'username'),
        )
        self.assertTrue(
            pwclientrc.has_option(self.project.linkname, 'password')
        )
        self.assertEqual(
            '<add your patchwork password here>',
            pwclientrc.get(self.project.linkname, 'password'),
        )
