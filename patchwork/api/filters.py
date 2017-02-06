# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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

from django_filters import FilterSet
from django_filters import IsoDateTimeFilter

from patchwork.models import Check
from patchwork.models import CoverLetter
from patchwork.models import Event
from patchwork.models import Patch
from patchwork.models import Series


class TimestampMixin(FilterSet):

    # TODO(stephenfin): These should filter on a 'updated_at' field instead
    before = IsoDateTimeFilter(name='date', lookup_expr='lt')
    since = IsoDateTimeFilter(name='date', lookup_expr='gte')


class SeriesFilter(TimestampMixin, FilterSet):

    class Meta:
        model = Series
        fields = ('submitter', 'project')


class CoverLetterFilter(TimestampMixin, FilterSet):

    class Meta:
        model = CoverLetter
        fields = ('project', 'series', 'submitter')


class PatchFilter(FilterSet):

    class Meta:
        model = Patch
        fields = ('project', 'series', 'submitter', 'delegate', 'state',
                  'archived')


class CheckFilter(TimestampMixin, FilterSet):

    class Meta:
        model = Check
        fields = ('user', 'state', 'context')


class EventFilter(FilterSet):

    class Meta:
        model = Event
        fields = ('project', 'series', 'patch', 'cover')
