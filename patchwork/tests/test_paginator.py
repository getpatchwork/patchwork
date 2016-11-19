# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

from django.core.urlresolvers import reverse
from django.test import TestCase

from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user

ITEMS_PER_PAGE = 1


class PaginatorTest(TestCase):

    def setUp(self):
        self.user = create_user()
        self.user.profile.items_per_page = ITEMS_PER_PAGE
        self.user.profile.save()
        self.project = create_project()
        self.patches = create_patches(10, project=self.project)

    def _get_patches(self, params):
        return self.client.get(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

    def test_items_per_page(self):
        response = self._get_patches({})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page'].object_list),
                         len(self.patches))

        self.client.force_login(self.user)
        response = self._get_patches({})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page'].object_list),
                         ITEMS_PER_PAGE)

    def test_page_valid(self):
        page = 2
        self.client.force_login(self.user)

        for page_ in [2, str(2)]:
            response = self._get_patches({'page': page_})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page'].object_list[0].id,
                             self.patches[-page].id)

    def test_page_invalid(self):
        self.client.force_login(self.user)
        response = self._get_patches({'page': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page'].object_list[0].id,
                         self.patches[-1].id)
