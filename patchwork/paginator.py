# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.core import paginator


DEFAULT_ITEMS_PER_PAGE = 100
LONG_PAGE_THRESHOLD = 30
LEADING_PAGE_RANGE_DISPLAYED = 4
TRAILING_PAGE_RANGE_DISPLAYED = 4
LEADING_PAGE_RANGE = 4
TRAILING_PAGE_RANGE = 2
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 1

# parts from:
#  http://blog.localkinegrinds.com/2007/09/06/digg-style-pagination-in-django/


class Paginator(paginator.Paginator):

    def __init__(self, request, objects):

        items_per_page = settings.DEFAULT_ITEMS_PER_PAGE

        if request.user.is_authenticated:
            items_per_page = request.user.profile.items_per_page

        super(Paginator, self).__init__(objects, items_per_page)

        try:
            page_no = int(request.GET.get('page', 1))
            self.current_page = self.page(int(page_no))
        except ValueError:
            page_no = 1
            self.current_page = self.page(page_no)
        except paginator.EmptyPage:
            if page_no < 1:
                page_no = 1
            else:
                page_no = self.num_pages
            self.current_page = self.page(page_no)

        self.leading_set = self.trailing_set = []

        pages = self.num_pages

        if pages <= LEADING_PAGE_RANGE_DISPLAYED:
            adjacent_start = 1
            adjacent_end = pages + 1
        elif page_no < LEADING_PAGE_RANGE:
            adjacent_start = 1
            adjacent_end = LEADING_PAGE_RANGE_DISPLAYED + 1
            self.leading_set = [n + pages for n in
                                range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif page_no >= pages - TRAILING_PAGE_RANGE:
            adjacent_start = pages - TRAILING_PAGE_RANGE_DISPLAYED + 1
            adjacent_end = pages + 1
            self.trailing_set = [n + 1 for n in
                                 range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else:
            adjacent_start = page_no - ADJACENT_PAGES
            adjacent_end = page_no + ADJACENT_PAGES + 1
            self.leading_set = [n + pages for n in
                                range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            self.trailing_set = [n + 1 for n in
                                 range(0, NUM_PAGES_OUTSIDE_RANGE)]

        self.adjacent_set = [n for n in range(adjacent_start, adjacent_end)
                             if n > 0 and n <= pages]

        self.leading_set.reverse()
        self.long_page = len(
            self.current_page.object_list) >= LONG_PAGE_THRESHOLD
