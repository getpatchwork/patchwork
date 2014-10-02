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
import random
import datetime
import string
import re
from django.test import TestCase
from django.test.client import Client
from patchwork.tests.utils import defaults, create_user, find_in_context
from patchwork.models import Person, Patch
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

class PatchOrderTest(TestCase):
    fixtures = ['default_states']

    d = datetime.datetime
    patchmeta = [
        ('AlCMyjOsx', 'AlxMyjOsx@nRbqkQV.wBw', d(2014,3,16,13, 4,50, 155643)), 
        ('MMZnrcDjT', 'MMmnrcDjT@qGaIfOl.tbk', d(2014,1,25,13, 4,50, 162814)), 
        ('WGirwRXgK', 'WGSrwRXgK@TriIETY.GhE', d(2014,2,14,13, 4,50, 169305)), 
        ('isjNIuiAc', 'issNIuiAc@OsEirYx.EJh', d(2014,3,15,13, 4,50, 176264)), 
        ('XkAQpYGws', 'XkFQpYGws@hzntTcm.JSE', d(2014,1,18,13, 4,50, 182493)), 
        ('uJuCPWMvi', 'uJACPWMvi@AVRBOBl.ecy', d(2014,3,12,13, 4,50, 189554)), 
        ('TyQmWtcbg', 'TylmWtcbg@DzrNeNH.JuB', d(2014,2, 3,13, 4,50, 195685)), 
        ('FpvAhWRdX', 'FpKAhWRdX@agxnCAI.wFO', d(2014,3,15,13, 4,50, 201398)), 
        ('bmoYvnyWa', 'bmdYvnyWa@aeoPnlX.juy', d(2014,3, 4,13, 4,50, 206800)), 
        ('CiReUQsAq', 'CiieUQsAq@DnOYRuf.TTI', d(2014,3,28,13, 4,50, 212169)),
    ]

    def setUp(self):
        defaults.project.save()

        for (name, email, date) in self.patchmeta:
            patch_name = 'testpatch' + name
            person = Person(name = name, email = email)
            person.save()
            patch = Patch(project = defaults.project, msgid = patch_name,
                        submitter = person, content = '', date = date)
            patch.save()

    def _extract_patch_ids(self, response):
        id_re = re.compile('<tr id="patch_row:(\d+)"')
        ids = [ int(m.group(1)) for m in id_re.finditer(response.content) ]
        return ids

    def _test_sequence(self, response, test_fn):
        ids = self._extract_patch_ids(response)
        self.assertTrue(bool(ids))
        patches = [ Patch.objects.get(id = i) for i in ids ]
        pairs = zip(patches, patches[1:])
        [ test_fn(p1, p2) for (p1, p2) in pairs ]

    def testDateOrder(self):
        url = reverse('patchwork.views.patch.list',
                kwargs={'project_id': defaults.project.linkname})
        response = self.client.get(url + '?order=date')
        def test_fn(p1, p2):
            self.assertLessEqual(p1.date, p2.date)
        self._test_sequence(response, test_fn)

    def testDateReverseOrder(self):
        url = reverse('patchwork.views.patch.list',
                kwargs={'project_id': defaults.project.linkname})
        response = self.client.get(url + '?order=-date')
        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.date, p2.date)
        self._test_sequence(response, test_fn)

    def testSubmitterOrder(self):
        url = reverse('patchwork.views.patch.list',
                kwargs={'project_id': defaults.project.linkname})
        response = self.client.get(url + '?order=submitter')
        def test_fn(p1, p2):
            self.assertLessEqual(p1.submitter.name.lower(),
                                 p2.submitter.name.lower())
        self._test_sequence(response, test_fn)

    def testSubmitterReverseOrder(self):
        url = reverse('patchwork.views.patch.list',
                kwargs={'project_id': defaults.project.linkname})
        response = self.client.get(url + '?order=-submitter')
        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.submitter.name.lower(),
                                    p2.submitter.name.lower())
        self._test_sequence(response, test_fn)

