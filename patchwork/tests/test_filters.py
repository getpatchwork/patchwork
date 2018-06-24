# Patchwork - automated patch tracking system
# Copyright (C) 2011 Jeremy Kerr <jk@ozlabs.org>
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
