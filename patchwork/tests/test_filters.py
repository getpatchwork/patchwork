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

import unittest

from django.test import TestCase
from django.test.client import Client

from patchwork.tests.utils import defaults, create_user, find_in_context


class FilterQueryStringTest(TestCase):
    def testFilterQSEscaping(self):
        """test that filter fragments in a query string are properly escaped,
           and stray ampersands don't get reflected back in the filter
           links"""
        project = defaults.project
        defaults.project.save()
        url = '/project/%s/list/?submitter=a%%26b=c' % project.linkname
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertNotContains(response, 'submitter=a&amp;b=c')
        self.assertNotContains(response, 'submitter=a&b=c')

    def testUTF8QSHandling(self):
        """test that non-ascii characters can be handled by the filter
           code"""
        project = defaults.project
        defaults.project.save()
        url = '/project/%s/list/?submitter=%%E2%%98%%83' % project.linkname
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
