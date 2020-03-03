# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_filters import rest_framework
from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django_filters import IsoDateTimeFilter
from django_filters import ModelMultipleChoiceFilter
from django.forms import ModelMultipleChoiceField as BaseMultipleChoiceField
from django.forms.widgets import MultipleHiddenInput
from rest_framework import exceptions

from patchwork.api import utils
from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Cover
from patchwork.models import Event
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import State


# custom backend

class DjangoFilterBackend(rest_framework.DjangoFilterBackend):

    def filter_queryset(self, request, queryset, view):
        try:
            return super().filter_queryset(request, queryset, view)
        except exceptions.ValidationError:
            return queryset.none()


# custom fields, filters

class ModelMultipleChoiceField(BaseMultipleChoiceField):

    def _get_filter(self, value):
        if not self.alternate_lookup:
            return 'pk', value

        try:
            return 'pk', int(value)
        except ValueError:
            return self.alternate_lookup, value

    def _check_values(self, value):
        """
        Given a list of possible PK values, returns a QuerySet of the
        corresponding objects. Raises a ValidationError if a given value is
        invalid (not a valid PK, not in the queryset, etc.)
        """
        # deduplicate given values to avoid creating many querysets or
        # requiring the database backend deduplicate efficiently.
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages['list'],
                code='list',
            )

        q_objects = Q()

        for pk in value:
            key, val = self._get_filter(pk)

            try:
                # NOTE(stephenfin): In contrast to the Django implementation
                # of this, we check to ensure each specified key exists and
                # fail if not. If we don't this, we can end up doing nothing
                # for the filtering which, to me, seems very confusing
                self.queryset.get(**{key: val})
            except (ValueError, TypeError, self.queryset.model.DoesNotExist):
                raise ValidationError(
                    self.error_messages['invalid_pk_value'],
                    code='invalid_pk_value',
                    params={'pk': val},
                )

            q_objects |= Q(**{key: val})

        qs = self.queryset.filter(q_objects)

        return qs


class BaseField(ModelMultipleChoiceField):

    alternate_lookup = None


class BaseFilter(ModelMultipleChoiceFilter):

    field_class = BaseField


class PersonChoiceField(ModelMultipleChoiceField):

    alternate_lookup = 'email__iexact'


class PersonFilter(ModelMultipleChoiceFilter):

    field_class = PersonChoiceField


class ProjectChoiceField(ModelMultipleChoiceField):

    alternate_lookup = 'linkname__iexact'


class ProjectFilter(ModelMultipleChoiceFilter):

    field_class = ProjectChoiceField


class StateChoiceField(ModelMultipleChoiceField):

    def _get_filter(self, value):
        try:
            return 'pk', int(value)
        except ValueError:
            return 'name__iexact', ' '.join(value.split('-'))


class StateFilter(ModelMultipleChoiceFilter):

    field_class = StateChoiceField


class UserChoiceField(ModelMultipleChoiceField):

    alternate_lookup = 'username__iexact'


class UserFilter(ModelMultipleChoiceFilter):

    field_class = UserChoiceField


# filter sets


class BaseFilterSet(FilterSet):

    @property
    def form(self):
        form = super(BaseFilterSet, self).form

        for version in getattr(self.Meta, 'versioned_fields', {}):
            if utils.has_version(self.request, version):
                continue

            for field in self.Meta.versioned_fields[version]:
                if field in form.fields:
                    del form.fields[field]

        return form


class TimestampMixin(BaseFilterSet):

    # TODO(stephenfin): These should filter on a 'updated_at' field instead
    before = IsoDateTimeFilter(lookup_expr='lt', field_name='date')
    since = IsoDateTimeFilter(lookup_expr='gte', field_name='date')


class SeriesFilterSet(TimestampMixin, BaseFilterSet):

    submitter = PersonFilter(queryset=Person.objects.all(), distinct=False)
    project = ProjectFilter(queryset=Project.objects.all(), distinct=False)

    class Meta:
        model = Series
        fields = ('submitter', 'project')


def msgid_filter(queryset, name, value):
    return queryset.filter(**{name: '<' + value + '>'})


class CoverFilterSet(TimestampMixin, BaseFilterSet):

    project = ProjectFilter(queryset=Project.objects.all(), distinct=False)
    # NOTE(stephenfin): We disable the select-based HTML widgets for these
    # filters as the resulting query is _huge_
    series = BaseFilter(queryset=Project.objects.all(),
                        widget=MultipleHiddenInput, distinct=False)
    submitter = PersonFilter(queryset=Person.objects.all(), distinct=False)
    msgid = CharFilter(method=msgid_filter)

    class Meta:
        model = Cover
        fields = ('project', 'series', 'submitter')


class PatchFilterSet(TimestampMixin, BaseFilterSet):

    project = ProjectFilter(queryset=Project.objects.all(), distinct=False)
    # NOTE(stephenfin): We disable the select-based HTML widgets for these
    # filters as the resulting query is _huge_
    series = BaseFilter(queryset=Series.objects.all(),
                        widget=MultipleHiddenInput, distinct=False)
    submitter = PersonFilter(queryset=Person.objects.all(), distinct=False)
    delegate = UserFilter(queryset=User.objects.all(), distinct=False)
    state = StateFilter(queryset=State.objects.all(), distinct=False)
    hash = CharFilter(lookup_expr='iexact')
    msgid = CharFilter(method=msgid_filter)

    class Meta:
        model = Patch
        # NOTE(dja): ideally we want to version the hash/msgid field, but I
        # can't find a way to do that which is reliable and not extremely ugly.
        # The best I can come up with is manually working with request.GET
        # which seems to rather defeat the point of using django-filters.
        fields = ('project', 'series', 'submitter', 'delegate',
                  'state', 'archived', 'hash', 'msgid')
        versioned_fields = {
            '1.2': ('hash', 'msgid'),
        }


class CheckFilterSet(TimestampMixin, BaseFilterSet):

    user = UserFilter(queryset=User.objects.all(), distinct=False)

    class Meta:
        model = Check
        fields = ('user', 'state', 'context')


class EventFilterSet(TimestampMixin, BaseFilterSet):

    # NOTE(stephenfin): We disable the select-based HTML widgets for these
    # filters as the resulting query is _huge_
    # TODO(stephenfin): We should really use an AJAX widget of some form here
    project = ProjectFilter(queryset=Project.objects.all(),
                            widget=MultipleHiddenInput,
                            distinct=False)
    series = BaseFilter(queryset=Series.objects.all(),
                        widget=MultipleHiddenInput,
                        distinct=False)
    patch = BaseFilter(queryset=Patch.objects.all(),
                       widget=MultipleHiddenInput,
                       distinct=False)
    cover = BaseFilter(queryset=Cover.objects.all(),
                       widget=MultipleHiddenInput,
                       distinct=False)

    class Meta:
        model = Event
        fields = ('project', 'category', 'series', 'patch', 'cover', 'actor')
        versioned_fields = {
            '1.2': ('actor', ),
        }


class BundleFilterSet(BaseFilterSet):

    project = ProjectFilter(queryset=Project.objects.all(), distinct=False)
    owner = UserFilter(queryset=User.objects.all(), distinct=False)

    class Meta:
        model = Bundle
        fields = ('project', 'owner', 'public')
