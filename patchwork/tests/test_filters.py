# Patchwork - automated patch tracking system
# Copyright (C) 2011 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_project


class FilterQueryStringTest(TestCase):

    def test_escaping(self):
        """Validate escaping of filter fragments in a query string.

        Stray ampersands should not get reflected back in the filter
        links.
        """
        project = create_project()
        url = reverse('patch-list', args=[project.linkname])

        response = self.client.get(url + '?submitter=a%%26b=c')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'submitter=a&amp;b=c')
        self.assertNotContains(response, 'submitter=a&b=c')

    def test_utf8_handling(self):
        """Validate handling of non-ascii characters."""
        project = create_project()
        url = reverse('patch-list', args=[project.linkname])

        response = self.client.get(url + '?submitter=%%E2%%98%%83')

        self.assertEqual(response.status_code, 200)
