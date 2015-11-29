# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
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

from django.conf import settings
from django.core import paginator
from django.utils.six.moves import range


DEFAULT_PATCHES_PER_PAGE = 100
LONG_PAGE_THRESHOLD = 30
LEADING_PAGE_RANGE_DISPLAYED = 4
TRAILING_PAGE_RANGE_DISPLAYED = 2
LEADING_PAGE_RANGE = 4
TRAILING_PAGE_RANGE = 2
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 1

# parts from:
#  http://blog.localkinegrinds.com/2007/09/06/digg-style-pagination-in-django/


class Paginator(paginator.Paginator):

    def __init__(self, request, objects):

        patches_per_page = settings.DEFAULT_PATCHES_PER_PAGE

        if request.user.is_authenticated():
            patches_per_page = request.user.profile.patches_per_page

        ppp = request.META.get('ppp')
        if ppp:
            try:
                patches_per_page = int(ppp)
            except ValueError:
                pass

        super(Paginator, self).__init__(objects, patches_per_page)

        try:
            page_no = int(request.GET.get('page'))
            self.current_page = self.page(int(page_no))
        except Exception:
            page_no = 1
            self.current_page = self.page(page_no)

        self.leading_set = self.trailing_set = []

        pages = self.num_pages

        if pages <= LEADING_PAGE_RANGE_DISPLAYED:
            adjacent_start = 1
            adjacent_end = pages + 1
        elif page_no <= LEADING_PAGE_RANGE:
            adjacent_start = 1
            adjacent_end = LEADING_PAGE_RANGE_DISPLAYED + 1
            self.leading_set = [n + pages for n in
                                range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif page_no > pages - TRAILING_PAGE_RANGE:
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
