# Patchwork - automated patch tracking system
# Copyright (C) 2013 Jeremy Kerr <jk@ozlabs.org>
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

from __future__ import absolute_import

import json

from django.test import TestCase
from django.urls import reverse
from django.utils.six.moves import range

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
