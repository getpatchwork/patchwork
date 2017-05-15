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

from django.core.exceptions import ValidationError
from django_filters import FilterSet
from django_filters import IsoDateTimeFilter
from django_filters import ModelChoiceFilter
from django.forms import ModelChoiceField

from patchwork.compat import LOOKUP_FIELD
from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import CoverLetter
from patchwork.models import Event
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import State


class TimestampMixin(FilterSet):

    # TODO(stephenfin): These should filter on a 'updated_at' field instead
    before = IsoDateTimeFilter(name='date', **{LOOKUP_FIELD: 'lt'})
    since = IsoDateTimeFilter(name='date', **{LOOKUP_FIELD: 'gte'})


class ProjectMixin(FilterSet):

    project = ModelChoiceFilter(to_field_name='linkname',
                                queryset=Project.objects.all())


class SeriesFilter(ProjectMixin, TimestampMixin, FilterSet):

    class Meta:
        model = Series
        fields = ('submitter', 'project')


class CoverLetterFilter(ProjectMixin, TimestampMixin, FilterSet):

    class Meta:
        model = CoverLetter
        fields = ('project', 'series', 'submitter')


class StateChoiceField(ModelChoiceField):

    def prepare_value(self, value):
        if hasattr(value, '_meta'):
            return value.slug
        else:
            return super(StateChoiceField, self).prepare_value(value)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            value = ' '.join(value.split('-'))
            value = self.queryset.get(name__iexact=value)
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise ValidationError(self.error_messages['invalid_choice'],
                                  code='invalid_choice')
        return value


class StateFilter(ModelChoiceFilter):

    field_class = StateChoiceField


class PatchFilter(ProjectMixin, FilterSet):

    state = StateFilter(queryset=State.objects.all())

    class Meta:
        model = Patch
        fields = ('project', 'series', 'submitter', 'delegate',
                  'state', 'archived')


class CheckFilter(TimestampMixin, FilterSet):

    class Meta:
        model = Check
        fields = ('user', 'state', 'context')


class EventFilter(ProjectMixin, FilterSet):

    class Meta:
        model = Event
        fields = ('project', 'category', 'series', 'patch', 'cover')


class BundleFilter(ProjectMixin, FilterSet):

    class Meta:
        model = Bundle
        fields = ('project', 'owner', 'public')
