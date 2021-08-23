# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import django
from django.contrib.auth.models import User
from django import forms
from django.forms import renderers
from django.db.models import Q
from django.db.utils import ProgrammingError
from django.template.backends import django as django_template_backend

from patchwork.models import Bundle
from patchwork.models import Patch
from patchwork.models import State
from patchwork.models import UserProfile


class PatchworkTableRenderer(renderers.EngineMixin, renderers.BaseRenderer):
    backend = django_template_backend.DjangoTemplates
    form_template_name = 'django/forms/table.html'
    formset_template_name = 'django/forms/formsets/table.html'


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    username = forms.RegexField(
        regex=r'^\w+$',
        max_length=30,
        label='Username',
    )
    email = forms.EmailField(max_length=100, label='Email address')
    password = forms.CharField(widget=forms.PasswordInput(), label='Password')

    def clean_username(self):
        value = self.cleaned_data['username']
        try:
            User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(
            'This username is already taken. Please choose another.'
        )

    def clean_email(self):
        value = self.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(
            'This email address is already in use '
            'for the account "%s".\n' % user.username
        )

    def clean(self):
        return self.cleaned_data


class BundleForm(forms.ModelForm):
    name = forms.RegexField(
        regex=r'^[^/]+$',
        min_length=1,
        max_length=50,
        required=False,
        error_messages={'invalid': "Bundle names can't contain slashes"},
        widget=forms.TextInput(
            attrs={'class': 'create-bundle', 'placeholder': 'Bundle name'}
        ),
    )

    class Meta:
        model = Bundle
        fields = ['name', 'public']


class CreateBundleForm(BundleForm):
    def clean_name(self):
        name = self.cleaned_data['name']
        if not name:
            raise forms.ValidationError(
                'No bundle name was specified', code='invalid'
            )

        count = Bundle.objects.filter(
            owner=self.instance.owner, name=name
        ).count()
        if count > 0:
            raise forms.ValidationError(
                'A bundle called %(name)s already exists',
                code='invalid',
                params={'name': name},
            )
        return name

    class Meta:
        model = Bundle
        fields = ['name']


class DeleteBundleForm(forms.Form):
    name = 'deletebundleform'
    form_name = forms.CharField(initial=name, widget=forms.HiddenInput)
    bundle_id = forms.IntegerField(widget=forms.HiddenInput)


class EmailForm(forms.Form):
    email = forms.EmailField(max_length=200)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['items_per_page', 'show_ids']
        labels = {'show_ids': 'Show Patch IDs:'}


def _get_delegate_qs(project, instance=None):
    if instance and not project:
        project = instance.project

    if not project:
        raise ValueError('Expected a project')

    q = Q(
        profile__in=UserProfile.objects.filter(maintainer_projects=project)
        .values('pk')
        .query
    )
    if instance and instance.delegate:
        q = q | Q(username=instance.delegate)

    return User.objects.complex_filter(q)


class PatchForm(forms.ModelForm):
    def __init__(self, instance=None, project=None, *args, **kwargs):
        super(PatchForm, self).__init__(instance=instance, *args, **kwargs)
        self.fields['delegate'] = forms.ModelChoiceField(
            queryset=_get_delegate_qs(project, instance),
            widget=forms.Select(attrs={'class': 'change-property-delegate'}),
            required=False,
        )

    class Meta:
        model = Patch
        fields = ['state', 'archived', 'delegate']
        widgets = {
            'state': forms.Select(attrs={'class': 'change-property-state'}),
            'archived': forms.CheckboxInput(
                attrs={'class': 'archive-patch-check'}
            ),
        }


class OptionalModelChoiceField(forms.ModelChoiceField):
    no_change_choice = ('*', 'No change')
    to_field_name = None

    def __init__(self, *args, placeholder, className, **kwargs):
        self.no_change_choice = ('*', placeholder)
        self.widget = forms.Select(attrs={'class': className})
        super(OptionalModelChoiceField, self).__init__(
            initial=self.no_change_choice[0], *args, **kwargs
        )

    def _get_choices(self):
        # _get_choices queries the database, which can fail if the db
        # hasn't been initialised yet. catch that and give an empty
        # set of choices for now.
        try:
            choices = list(
                super(OptionalModelChoiceField, self)._get_choices()
            )
        except ProgrammingError:
            choices = []
        choices.append(self.no_change_choice)
        return choices

    if django.VERSION >= (5, 0):
        choices = property(_get_choices, forms.ChoiceField.choices.fset)
    else:
        choices = property(_get_choices, forms.ChoiceField._set_choices)

    def is_no_change(self, value):
        return value == self.no_change_choice[0]

    def clean(self, value):
        if value == self.no_change_choice[0]:
            return value
        return super(OptionalModelChoiceField, self).clean(value)


class OptionalBooleanField(forms.TypedChoiceField):
    def __init__(self, className, *args, **kwargs):
        self.widget = forms.Select(attrs={'class': className})
        super(OptionalBooleanField, self).__init__(*args, **kwargs)

    def is_no_change(self, value):
        return value == self.empty_value


class MultiplePatchForm(forms.Form):
    action = 'update'
    archived = OptionalBooleanField(
        className='archive-patch-select',
        choices=[
            ('*', 'No change'),
            ('True', 'Archive'),
            ('False', 'Unarchive'),
        ],
        coerce=lambda x: x == 'True',
        empty_value='*',
        label='Archived',
    )

    def __init__(self, project, *args, **kwargs):
        super(MultiplePatchForm, self).__init__(*args, **kwargs)
        self.fields['delegate'] = OptionalModelChoiceField(
            queryset=_get_delegate_qs(project=project),
            placeholder='Delegate to',
            className='change-property-delegate',
            label='Delegate to',
            required=False,
        )
        self.fields['state'] = OptionalModelChoiceField(
            queryset=State.objects.all(),
            placeholder='Change state',
            className='change-property-state',
            label='Change state',
        )

    def save(self, instance, commit=True):
        opts = instance.__class__._meta
        if self.errors:
            raise ValueError(
                'The %s could not be changed because the data '
                "didn't validate." % opts.object_name
            )
        data = self.cleaned_data
        # Update the instance
        for f in opts.fields:
            if f.name not in data:
                continue

            field = self.fields.get(f.name, None)
            if not field:
                continue

            if field.is_no_change(data[f.name]):
                continue

            setattr(instance, f.name, data[f.name])

        if commit:
            instance.save()
        return instance
