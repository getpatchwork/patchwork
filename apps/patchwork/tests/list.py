# Patchwork - automated patch tracking system
# Copyright (C) 2012 Jeremy Kerr <jk@ozlabs.org>
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
from django.core.urlresolvers import reverse

class EmptyPatchListTest(TestCase):

    def testEmptyPatchList(self):
        """test that we don't output an empty table when there are no
           patches present"""
        project = defaults.project
        defaults.project.save()
        url = reverse('patchwork.views.patch.list',
                kwargs={'project_id': project.linkname})
        response = self.client.get(url)
        self.assertContains(response, 'No patches to display')
        self.assertNotContains(response, 'tbody')

