# Patchwork - automated patch tracking system
# Copyright (C) 2013 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import json

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_person


class SubmitterCompletionTest(TestCase):

    """Validate the 'submitter' autocomplete endpoint."""

    def test_name_complete(self):
        people = [create_person(name='Test name'), create_person(name=None)]
        response = self.client.get(reverse('api-submitters'), {'q': 'name'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], people[0].name)

    def test_email_complete(self):
        people = [create_person(email='test1@example.com'),
                  create_person(email='test2@example.com')]
        response = self.client.get(reverse('api-submitters'), {'q': 'test2'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['email'], people[1].email)

    def test_param_limit(self):
        for i in range(10):
            create_person()
        response = self.client.get(reverse('api-submitters'),
                                   {'q': 'test', 'l': 5})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 5)
