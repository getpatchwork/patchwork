# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

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

        self.client.login(username=self.user.username,
                          password=self.user.username)
        response = self._get_patches({})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page'].object_list),
                         ITEMS_PER_PAGE)

    def test_page_valid(self):
        page = 2
        self.client.login(username=self.user.username,
                          password=self.user.username)

        for page_ in [2, str(2)]:
            response = self._get_patches({'page': page_})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page'].object_list[0].id,
                             self.patches[-page].id)

    def test_navigation(self):
        self.client.login(username=self.user.username,
                          password=self.user.username)
        for page_num in range(1, 11):
            response = self._get_patches({'page': page_num})

            page = response.context['page']
            leading = page.paginator.leading_set
            adjacent = page.paginator.adjacent_set
            trailing = page.paginator.trailing_set

            # if there is a prev page, it should be:
            if page.has_previous():
                self.assertEqual(page.previous_page_number(),
                                 page_num - 1)
                # ... either in the adjacent set or in the trailing set
                if adjacent is not None:
                    self.assertIn(page_num - 1, adjacent)
                else:
                    self.assertIn(page_num - 1, trailing)

            # if there is a next page, it should be:
            if page.has_next():
                self.assertEqual(page.next_page_number(),
                                 page_num + 1)
                # ... either in the adjacent set or in the leading set
                if adjacent is not None:
                    self.assertIn(page_num + 1, adjacent)
                else:
                    self.assertIn(page_num + 1, leading)

            # no page number should appear more than once
            for x in adjacent:
                self.assertNotIn(x, leading)
                self.assertNotIn(x, trailing)
            for x in leading:
                self.assertNotIn(x, trailing)

    def test_page_invalid(self):
        self.client.login(username=self.user.username,
                          password=self.user.username)
        response = self._get_patches({'page': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page'].object_list[0].id,
                         self.patches[-1].id)
