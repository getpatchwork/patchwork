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


from django.contrib.auth.models import User
from django import forms

from patchwork.models import RegistrationRequest, Patch, State, Bundle, \
         UserProfile

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget = forms.PasswordInput)
    email = forms.EmailField(max_length = 200)

    class Meta:
        model = RegistrationRequest
        exclude = ['key', 'active', 'date']

    def clean_email(self):
        value = self.cleaned_data['email']
        try:
            User.objects.get(email = value)
            raise forms.ValidationError(('The email address %s has ' +
                    'has already been registered') % value)
        except User.DoesNotExist:
            pass
        try:
            RegistrationRequest.objects.get(email = value)
            raise forms.ValidationError(('The email address %s has ' +
                    'has already been registered') % value)
        except RegistrationRequest.DoesNotExist:
            pass
        return value

    def clean_username(self):
        value = self.cleaned_data['username']
        try:
            User.objects.get(username = value)
            raise forms.ValidationError(('The username %s has ' +
                    'has already been registered') % value)
        except User.DoesNotExist:
            pass
        try:
            RegistrationRequest.objects.get(username = value)
            raise forms.ValidationError(('The username %s has ' +
                    'has already been registered') % value)
        except RegistrationRequest.DoesNotExist:
            pass
        return value

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 30)
    password = forms.CharField(widget = forms.PasswordInput)

class BundleForm(forms.ModelForm):
    class Meta:
        model = Bundle
        fields = ['name', 'public']

class CreateBundleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateBundleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Bundle
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name']
        count = Bundle.objects.filter(owner = self.instance.owner, \
                name = name).count()
        if count > 0:
            raise forms.ValidationError('A bundle called %s already exists' \
                    % name)
        return name

class DelegateField(forms.ModelChoiceField):
    def __init__(self, project, *args, **kwargs):
	queryset = User.objects.filter(userprofile__in = \
                UserProfile.objects \
                        .filter(maintainer_projects = project) \
                        .values('pk').query)
        super(DelegateField, self).__init__(queryset, *args, **kwargs)


class PatchForm(forms.ModelForm):
    def __init__(self, instance = None, project = None, *args, **kwargs):
	if (not project) and instance:
            project = instance.project
        if not project:
	    raise Exception("meep")
        super(PatchForm, self).__init__(instance = instance, *args, **kwargs)
        self.fields['delegate'] = DelegateField(project)

    class Meta:
        model = Patch
        fields = ['state', 'archived', 'delegate']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['primary_project', 'patches_per_page']

class OptionalDelegateField(DelegateField):
    no_change_choice = ('*', 'no change')

    def __init__(self, no_change_choice = None, *args, **kwargs):
        self.filter = None
        if (no_change_choice):
            self.no_change_choice = no_change_choice
        super(OptionalDelegateField, self). \
            __init__(initial = self.no_change_choice[0], *args, **kwargs)

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

    def __init__(self, no_change_choice = None, *args, **kwargs):
        self.filter = None
        if (no_change_choice):
            self.no_change_choice = no_change_choice
        super(OptionalModelChoiceField, self). \
            __init__(initial = self.no_change_choice[0], *args, **kwargs)

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

class MultiplePatchForm(PatchForm):
    state = OptionalModelChoiceField(queryset = State.objects.all())
    archived = MultipleBooleanField()

    def __init__(self, project, *args, **kwargs):
        super(MultiplePatchForm, self).__init__(project = project,
                *args, **kwargs)
        self.fields['delegate'] = OptionalDelegateField(project = project)

    def save(self, instance, commit = True):
        opts = instance.__class__._meta
        if self.errors:
            raise ValueError("The %s could not be changed because the data "
                    "didn't validate." % opts.object_name)
        data = self.cleaned_data
        # remove 'no change fields' from the data
        for f in opts.fields:
            if not f.name in data:
                continue

            field = getattr(self, f.name, None)
            if not field:
                continue

            if field.is_no_change(data[f.name]):
                del data[f.name]

        return forms.save_instance(self, instance,
                self._meta.fields, 'changed', commit)

class UserPersonLinkForm(forms.Form):
    email = forms.EmailField(max_length = 200)
