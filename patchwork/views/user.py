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

import smtplib

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.compat import render_to_string
from patchwork.compat import reverse
from patchwork.filters import DelegateFilter
from patchwork.forms import EmailForm
from patchwork.forms import RegistrationForm
from patchwork.forms import UserProfileForm
from patchwork.models import Bundle
from patchwork.models import EmailConfirmation
from patchwork.models import EmailOptout
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import State
from patchwork.views import generic_list
from patchwork.views import utils


def register(request):
    context = {}

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # create inactive user
            user = auth.models.User.objects.create_user(data['username'],
                                                        data['email'],
                                                        data['password'])
            user.is_active = False
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.save()

            # create confirmation
            conf = EmailConfirmation(type='registration', user=user,
                                     email=user.email)
            conf.save()

            # send email
            subject = 'Patchwork account confirmation'
            message = render_to_string(
                'patchwork/activation_email.txt',
                {'site': Site.objects.get_current(), 'confirmation': conf})

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                      [conf.email])

            # setting 'confirmation' in the template indicates success
            context['confirmation'] = conf
    else:
        form = RegistrationForm()

    context['form'] = form

    return render(request, 'patchwork/registration_form.html', context)


def register_confirm(request, conf):
    conf.user.is_active = True
    conf.user.save()
    conf.deactivate()

    try:
        person = Person.objects.get(email__iexact=conf.user.email)
    except Person.DoesNotExist:
        person = Person(email=conf.user.email,
                        name=conf.user.profile.name)
    person.user = conf.user
    person.save()

    return render(request, 'patchwork/registration-confirm.html')


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(instance=request.user.profile,
                               data=request.POST)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=request.user.profile)

    # TODO(stephenfin): Add a related_name for User->Bundle
    context = {
        'bundles': Bundle.objects.filter(owner=request.user),
        'profileform': form,
    }

    # FIXME(stephenfin): This looks unsafe. Investigate.
    optout_query = '%s.%s IN (SELECT %s FROM %s)' % (
        Person._meta.db_table,
        Person._meta.get_field('email').column,
        EmailOptout._meta.get_field('email').column,
        EmailOptout._meta.db_table)
    people = Person.objects.filter(user=request.user) \
        .extra(select={'is_optout': optout_query})
    context['linked_emails'] = people
    context['linkform'] = EmailForm()
    context['api_token'] = request.user.profile.token
    if settings.ENABLE_REST_API:
        context['rest_api_enabled'] = True

    return render(request, 'patchwork/profile.html', context)


@login_required
def link(request):
    context = {}

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            conf = EmailConfirmation(type='userperson',
                                     user=request.user,
                                     email=form.cleaned_data['email'])
            conf.save()

            context['confirmation'] = conf

            try:
                send_mail('Patchwork email address confirmation',
                          render_to_string('patchwork/user-link.mail',
                                           context, request=request),
                          settings.DEFAULT_FROM_EMAIL,
                          [form.cleaned_data['email']])
            except smtplib.SMTPException:
                context['confirmation'] = None
                context['error'] = ('An error occurred during confirmation. '
                                    'Please try again later')
    else:
        form = EmailForm()

    context['linkform'] = form

    return render(request, 'patchwork/user-link.html', context)


@login_required
def link_confirm(request, conf):
    try:
        person = Person.objects.get(email__iexact=conf.email)
    except Person.DoesNotExist:
        person = Person(email=conf.email)

    person.link_to_user(conf.user)
    person.save()
    conf.deactivate()

    context = {
        'person': person,
    }

    return render(request, 'patchwork/user-link-confirm.html', context)


@login_required
def unlink(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    if request.method == 'POST' and person.email != request.user.email:
        person.user = None
        person.save()

    return HttpResponseRedirect(reverse('user-profile'))


@login_required
def todo_lists(request):
    todo_lists = []

    for project in Project.objects.all():
        patches = request.user.profile.todo_patches(project=project)
        if not patches.count():
            continue

        todo_lists.append({'project': project, 'n_patches': patches.count()})

    if len(todo_lists) == 1:
        return HttpResponseRedirect(
            reverse(
                'user-todo',
                kwargs={'project_id': todo_lists[0]['project'].linkname}))

    context = {
        'todo_lists': todo_lists,
    }

    return render(request, 'patchwork/todo-lists.html', context)


@login_required
def todo_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    patches = request.user.profile.todo_patches(project=project)
    filter_settings = [(DelegateFilter,
                        {'delegate': request.user})]

    # TODO(stephenfin): Build the context dict here
    context = generic_list(request, project,
                           'user-todo',
                           view_args={'project_id': project.linkname},
                           filter_settings=filter_settings,
                           patches=patches)

    context['action_required_states'] = \
        State.objects.filter(action_required=True).all()
    return render(request, 'patchwork/todo-list.html', context)


@login_required
def generate_token(request):
    utils.regenerate_token(request.user)
    return HttpResponseRedirect(reverse('user-profile'))
