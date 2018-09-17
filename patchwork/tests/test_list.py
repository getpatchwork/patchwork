# Patchwork - automated patch tracking system
# Copyright (C) 2012 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt
import re

from django.test import TestCase
from django.urls import reverse
from django.utils.six.moves import zip

from patchwork.models import Patch
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project


class EmptyPatchListTest(TestCase):

    def test_empty_patch_list(self):
        """Validates absence of table with zero patches."""
        project = create_project()
        url = reverse('patch-list', kwargs={'project_id': project.linkname})
        response = self.client.get(url)
        self.assertContains(response, 'No patches to display')


class PatchOrderTest(TestCase):

    patchmeta = [
        ('AlCMyjOsx', 'AlxMyjOsx@nRbqkQV.wBw',
         dt(2014, 3, 16, 13, 4, 50, 155643)),
        ('MMZnrcDjT', 'MMmnrcDjT@qGaIfOl.tbk',
         dt(2014, 1, 25, 13, 4, 50, 162814)),
        ('WGirwRXgK', 'WGSrwRXgK@TriIETY.GhE',
         dt(2014, 2, 14, 13, 4, 50, 169305)),
        ('isjNIuiAc', 'issNIuiAc@OsEirYx.EJh',
         dt(2014, 3, 15, 13, 4, 50, 176264)),
        ('XkAQpYGws', 'XkFQpYGws@hzntTcm.JSE',
         dt(2014, 1, 18, 13, 4, 50, 182493)),
        ('uJuCPWMvi', 'uJACPWMvi@AVRBOBl.ecy',
         dt(2014, 3, 12, 13, 4, 50, 189554)),
        ('TyQmWtcbg', 'TylmWtcbg@DzrNeNH.JuB',
         dt(2014, 2, 3, 13, 4, 50, 195685)),
        ('FpvAhWRdX', 'FpKAhWRdX@agxnCAI.wFO',
         dt(2014, 3, 15, 13, 4, 50, 201398)),
        ('bmoYvnyWa', 'bmdYvnyWa@aeoPnlX.juy',
         dt(2014, 3, 4, 13, 4, 50, 206800)),
        ('CiReUQsAq', 'CiieUQsAq@DnOYRuf.TTI',
         dt(2014, 3, 28, 13, 4, 50, 212169)),
    ]

    def setUp(self):
        self.project = create_project()

        for name, email, date in self.patchmeta:
            person = create_person(name=name, email=email)
            create_patch(submitter=person, project=self.project,
                         date=date)

    def _extract_patch_ids(self, response):
        id_re = re.compile(r'<tr id="patch_row:(\d+)"')
        ids = [int(m.group(1))
               for m in id_re.finditer(response.content.decode())]

        return ids

    def _test_sequence(self, response, test_fn):
        ids = self._extract_patch_ids(response)
        self.assertTrue(bool(ids))
        patches = [Patch.objects.get(id=i) for i in ids]
        pairs = list(zip(patches, patches[1:]))

        for p1, p2 in pairs:
            test_fn(p1, p2)

    def test_date_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=date')

        def test_fn(p1, p2):
            self.assertLessEqual(p1.date, p2.date)

        self._test_sequence(response, test_fn)

    def test_date_reverse_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=-date')

        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.date, p2.date)

        self._test_sequence(response, test_fn)

    def test_submitter_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=submitter')

        def test_fn(p1, p2):
            self.assertLessEqual(p1.submitter.name.lower(),
                                 p2.submitter.name.lower())

        self._test_sequence(response, test_fn)

    def test_submitter_reverse_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=-submitter')

        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.submitter.name.lower(),
                                    p2.submitter.name.lower())

        self._test_sequence(response, test_fn)
