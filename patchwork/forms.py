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

from django.contrib.auth.models import User
from django import forms

from patchwork.models import Patch, State, Bundle, UserProfile


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    username = forms.RegexField(regex=r'^\w+$', max_length=30,
                                label=u'Username')
    email = forms.EmailField(max_length=100, label=u'Email address')
    password = forms.CharField(widget=forms.PasswordInput(),
                               label='Password')

    def clean_username(self):
        value = self.cleaned_data['username']
        try:
            user = User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError('This username is already taken. ' +
                                    'Please choose another.')

    def clean_email(self):
        value = self.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError('This email address is already in use ' +
                                    'for the account "%s".\n' % user.username)

    def clean(self):
        return self.cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)


class BundleForm(forms.ModelForm):
    name = forms.RegexField(regex=r'^[^/]+$', max_length=50, label=u'Name',
                            error_messages={'invalid': 'Bundle names can\'t contain slashes'})

    class Meta:
        model = Bundle
        fields = ['name', 'public']


class CreateBundleForm(BundleForm):

    def __init__(self, *args, **kwargs):
        super(CreateBundleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Bundle
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name']
        count = Bundle.objects.filter(owner=self.instance.owner,
                                      name=name).count()
        if count > 0:
            raise forms.ValidationError('A bundle called %s already exists'
                                        % name)
        return name


class DeleteBundleForm(forms.Form):
    name = 'deletebundleform'
    form_name = forms.CharField(initial=name, widget=forms.HiddenInput)
    bundle_id = forms.IntegerField(widget=forms.HiddenInput)


class DelegateField(forms.ModelChoiceField):

    def __init__(self, project, *args, **kwargs):
        queryset = User.objects.filter(profile__in=UserProfile.objects
                                       .filter(maintainer_projects=project)
                                       .values('pk').query)
        super(DelegateField, self).__init__(queryset, *args, **kwargs)


class PatchForm(forms.ModelForm):

    def __init__(self, instance=None, project=None, *args, **kwargs):
        if (not project) and instance:
            project = instance.project
        if not project:
            raise Exception("meep")
        super(PatchForm, self).__init__(instance=instance, *args, **kwargs)
        self.fields['delegate'] = DelegateField(project, required=False)

    class Meta:
        model = Patch
        fields = ['state', 'archived', 'delegate']


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['primary_project', 'patches_per_page']


class OptionalDelegateField(DelegateField):
    no_change_choice = ('*', 'no change')
    to_field_name = None

    def __init__(self, no_change_choice=None, *args, **kwargs):
        self.filter = None
        if (no_change_choice):
            self.no_change_choice = no_change_choice
        super(OptionalDelegateField, self). \
            __init__(initial=self.no_change_choice[0], *args, **kwargs)

    def _get_choices(self):
        choices = list(
            super(OptionalDelegateField, self)._get_choices())
        choices.append(self.no_change_choice)
        return choices

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def is_no_change(self, value):
        return value == self.no_change_choice[0]

    def clean(self, value):
        if value == self.no_change_choice[0]:
            return value
        return super(OptionalDelegateField, self).clean(value)


class OptionalModelChoiceField(forms.ModelChoiceField):
    no_change_choice = ('*', 'no change')
    to_field_name = None

    def __init__(self, no_change_choice=None, *args, **kwargs):
        self.filter = None
        if (no_change_choice):
            self.no_change_choice = no_change_choice
        super(OptionalModelChoiceField, self). \
            __init__(initial=self.no_change_choice[0], *args, **kwargs)

    def _get_choices(self):
        choices = list(
            super(OptionalModelChoiceField, self)._get_choices())
        choices.append(self.no_change_choice)
        return choices

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def is_no_change(self, value):
        return value == self.no_change_choice[0]

    def clean(self, value):
        if value == self.no_change_choice[0]:
            return value
        return super(OptionalModelChoiceField, self).clean(value)


class MultipleBooleanField(forms.ChoiceField):
    no_change_choice = ('*', 'no change')

    def __init__(self, *args, **kwargs):
        super(MultipleBooleanField, self).__init__(*args, **kwargs)
        self.choices = [self.no_change_choice] + \
            [(True, 'Archived'), (False, 'Unarchived')]

    def is_no_change(self, value):
        return value == self.no_change_choice[0]

    # TODO: Check whether it'd be worth to use a TypedChoiceField here; I
    # think that'd allow us to get rid of the custom valid_value() and
    # to_python() methods.
    def valid_value(self, value):
        if value in [v1 for (v1, v2) in self.choices]:
            return True
        return False

    def to_python(self, value):
        if value is None or self.is_no_change(value):
            return self.no_change_choice[0]
        elif value == 'True':
            return True
        elif value == 'False':
            return False
        else:
            raise ValueError('Unknown value: %s' % value)


class MultiplePatchForm(forms.Form):
    action = 'update'
    state = OptionalModelChoiceField(queryset=State.objects.all())
    archived = MultipleBooleanField()

    def __init__(self, project, *args, **kwargs):
        super(MultiplePatchForm, self).__init__(*args, **kwargs)
        self.fields['delegate'] = OptionalDelegateField(project=project,
                                                        required=False)

    def save(self, instance, commit=True):
        opts = instance.__class__._meta
        if self.errors:
            raise ValueError("The %s could not be changed because the data "
                             "didn't validate." % opts.object_name)
        data = self.cleaned_data
        # Update the instance
        for f in opts.fields:
            if not f.name in data:
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


class EmailForm(forms.Form):
    email = forms.EmailField(max_length=200)

UserPersonLinkForm = EmailForm
OptinoutRequestForm = EmailForm
