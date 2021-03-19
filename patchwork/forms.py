# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.auth.models import User
from django.core import exceptions
from django import forms
from django.db.models import Q
from django.db.utils import ProgrammingError

from patchwork import models
from patchwork.models import Bundle
from patchwork.models import Patch
from patchwork.models import State
from patchwork.models import UserProfile


class RegistrationForm(forms.Form):

    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    username = forms.RegexField(
        regex=r'^\w+$', max_length=30, label='Username'
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
        label='Name',
        error_messages={'invalid': 'Bundle names can\'t contain slashes'},
    )

    class Meta:
        model = Bundle
        fields = ['name', 'public']


class CreateBundleForm(BundleForm):

    def clean_name(self):
        name = self.cleaned_data['name']
        count = Bundle.objects.filter(
            owner=self.instance.owner, name=name
        ).count()
        if count > 0:
            raise forms.ValidationError(
                'A bundle called %s already exists' % name
            )
        return name

    class Meta:
        model = Bundle
        fields = ['name']


class DeleteBundleForm(forms.Form):

    name = 'deletebundleform'
    form_name = forms.CharField(initial=name, widget=forms.HiddenInput)
    bundle_id = forms.IntegerField(widget=forms.HiddenInput)


class UserForm(forms.ModelForm):

    name = 'user-form'

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class EmailForm(forms.Form):

    email = forms.EmailField(max_length=200)


class UserLinkEmailForm(forms.Form):

    name = 'user-link-email-form'

    email = forms.EmailField(max_length=200)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        # ensure this email is not already linked to our account
        try:
            models.Person.objects.get(email=email, user=self.user)
        except models.Person.DoesNotExist:
            pass
        else:
            raise exceptions.ValidationError(
                "That email is already linked to your account."
            )

        return email


class UserUnlinkEmailForm(forms.Form):

    name = 'user-unlink-email-form'

    email = forms.EmailField(max_length=200)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        # ensure we're not unlinking the final email
        if email == self.user.email:
            raise exceptions.ValidationError(
                "You can't unlink your primary email."
            )

        # and that this email is in fact our email to unlink
        try:
            models.Person.objects.get(email=email, user=self.user)
        except models.Person.DoesNotExist:
            raise exceptions.ValidationError(
                "That email is not linked to your account."
            )

        return email


class UserPrimaryEmailForm(forms.ModelForm):

    name = 'user-primary-email-form'

    class Meta:
        model = User
        fields = ['email']


class UserEmailOptinForm(forms.Form):

    name = 'user-email-optin-form'

    email = forms.EmailField(max_length=200)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        # ensure this email is linked to our account
        try:
            models.Person.objects.get(email=email, user=self.user)
        except models.Person.DoesNotExist:
            raise exceptions.ValidationError(
                "You can't configure mail preferences for an email that is "
                "not associated with your account."
            )

        return email


class UserEmailOptoutForm(forms.Form):

    name = 'user-email-optout-form'

    email = forms.EmailField(max_length=200)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        # ensure this email is linked to our account
        try:
            models.Person.objects.get(email=email, user=self.user)
        except models.Person.DoesNotExist:
            raise exceptions.ValidationError(
                "You can't configure mail preferences for an email that is "
                "not associated with your account"
            )

        try:
            models.EmailOptout.objects.get(email=email)
        except models.EmailOptout.DoesNotExist:
            pass
        else:
            raise exceptions.ValidationError(
                "You have already opted out of emails to this address."
            )

        return email


class UserProfileForm(forms.ModelForm):

    name = 'user-profile-form'
    show_ids = forms.TypedChoiceField(
        coerce=lambda x: x == 'yes',
        choices=(('yes', 'Yes'), ('no', 'No')),
        widget=forms.RadioSelect,
    )

    class Meta:
        model = UserProfile
        fields = ['items_per_page', 'show_ids']
        labels = {'show_ids': 'Show Patch IDs:'}


class AddProjectMaintainerForm(forms.Form):

    name = 'add-maintainer'

    username = forms.RegexField(
        regex=r'^\w+$', max_length=30, label='Username'
    )

    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def clean_username(self):
        value = self.cleaned_data['username']

        try:
            user = User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            raise forms.ValidationError(
                'That username is not valid. Please choose another.'
            )

        if self.project in user.profile.maintainer_projects.all():
            raise forms.ValidationError(
                'That user is already a maintainer of this project.'
            )

        return value


class RemoveProjectMaintainerForm(forms.Form):

    name = 'remove-maintainer'

    username = forms.RegexField(
        regex=r'^\w+$', max_length=30, label='Username'
    )

    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def clean_username(self):
        value = self.cleaned_data['username']

        try:
            user = User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            raise forms.ValidationError(
                'That username is not valid. Please choose another.'
            )

        maintainers = User.objects.filter(
            profile__maintainer_projects=self.project,
        ).select_related('profile')

        if user not in maintainers:
            raise forms.ValidationError(
                'That user is not a maintainer of this project.'
            )

        # TODO(stephenfin): Should we prevent users removing themselves?

        if maintainers.count() <= 1:
            raise forms.ValidationError(
                'You cannot remove the only maintainer of the project.'
            )

        return value


class ProjectSettingsForm(forms.ModelForm):

    name = 'project-settings'

    class Meta:
        model = models.Project
        fields = [
            'name', 'web_url', 'scm_url', 'webscm_url', 'list_archive_url',
            'list_archive_url_format', 'commit_url_format',
        ]


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
            queryset=_get_delegate_qs(project, instance), required=False
        )

    class Meta:
        model = Patch
        fields = ['state', 'archived', 'delegate']


class OptionalModelChoiceField(forms.ModelChoiceField):

    no_change_choice = ('*', 'no change')
    to_field_name = None

    def __init__(self, *args, **kwargs):
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

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def is_no_change(self, value):
        return value == self.no_change_choice[0]

    def clean(self, value):
        if value == self.no_change_choice[0]:
            return value
        return super(OptionalModelChoiceField, self).clean(value)


class OptionalBooleanField(forms.TypedChoiceField):
    def is_no_change(self, value):
        return value == self.empty_value


class MultiplePatchForm(forms.Form):

    action = 'update'
    archived = OptionalBooleanField(
        choices=[
            ('*', 'no change'),
            ('True', 'Archived'),
            ('False', 'Unarchived'),
        ],
        coerce=lambda x: x == 'True',
        empty_value='*',
    )

    def __init__(self, project, *args, **kwargs):
        super(MultiplePatchForm, self).__init__(*args, **kwargs)
        self.fields['delegate'] = OptionalModelChoiceField(
            queryset=_get_delegate_qs(project=project), required=False
        )
        self.fields['state'] = OptionalModelChoiceField(
            queryset=State.objects.all()
        )

    def save(self, instance, commit=True):
        opts = instance.__class__._meta
        if self.errors:
            raise ValueError(
                "The %s could not be changed because the data "
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
