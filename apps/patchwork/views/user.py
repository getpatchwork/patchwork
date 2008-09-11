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


from django.contrib.auth.decorators import login_required
from patchwork.requestcontext import PatchworkRequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect
from patchwork.models import Project, Patch, Bundle, Person, UserProfile, \
         UserPersonConfirmation, State
from patchwork.forms import MultiplePatchForm, UserProfileForm, \
         UserPersonLinkForm
from patchwork.utils import Order, get_patch_ids
from patchwork.filters import DelegateFilter
from patchwork.paginator import Paginator
from patchwork.views import generic_list
from django.template.loader import render_to_string
from django.template import Context
from django.conf import settings
from django.core.mail import send_mail
import django.core.urlresolvers

@login_required
def profile(request):
    context = PatchworkRequestContext(request)

    if request.method == 'POST':
        form = UserProfileForm(instance = request.user.get_profile(),
                data = request.POST)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance = request.user.get_profile())

    context.project = request.user.get_profile().primary_project
    context['bundles'] = Bundle.objects.filter(owner = request.user)
    context['profileform'] = form

    people = Person.objects.filter(user = request.user)
    context['linked_emails'] = people
    context['linkform'] = UserPersonLinkForm()

    return render_to_response('patchwork/profile.html', context)

@login_required
def link(request):
    context = PatchworkRequestContext(request)

    form = UserPersonLinkForm(request.POST)
    if request.method == 'POST':
        form = UserPersonLinkForm(request.POST)
        if form.is_valid():
            conf = UserPersonConfirmation(user = request.user,
                    email = form.cleaned_data['email'])
            conf.save()
            context['confirmation'] = conf

            try:
                send_mail('Patchwork email address confirmation',
                            render_to_string('patchwork/user-link.mail',
                                context),
                            settings.DEFAULT_FROM_EMAIL,
                            [form.cleaned_data['email']])
            except Exception, ex:
                context['confirmation'] = None
                context['error'] = 'An error occurred during confirmation. ' + \
                                   'Please try again later'
    context['linkform'] = form

    return render_to_response('patchwork/user-link.html', context)

@login_required
def link_confirm(request, key):
    context = PatchworkRequestContext(request)
    confirmation = get_object_or_404(UserPersonConfirmation, key = key)

    errors = confirmation.confirm()
    if errors:
        context['errors'] = errors
    else:
        context['person'] = Person.objects.get(email = confirmation.email)

    return render_to_response('patchwork/user-link-confirm.html', context)

@login_required
def unlink(request, person_id):
    context = PatchworkRequestContext(request)
    person = get_object_or_404(Person, id = person_id)

    if request.method == 'POST':
        if person.email != request.user.email:
            person.user = None
            person.save()

    url = django.core.urlresolvers.reverse('patchwork.views.user.profile')
    return HttpResponseRedirect(url)


@login_required
def todo_lists(request):
    todo_lists = []

    for project in Project.objects.all():
        patches = request.user.get_profile().todo_patches(project = project)
        if not patches.count():
            continue

        todo_lists.append({'project': project, 'n_patches': patches.count()})

    if len(todo_lists) == 1:
        return todo_list(request, todo_lists[0]['project'].linkname)

    context = PatchworkRequestContext(request)
    context['todo_lists'] = todo_lists
    context.project = request.user.get_profile().primary_project
    return render_to_response('patchwork/todo-lists.html', context)

@login_required
def todo_list(request, project_id):
    project = get_object_or_404(Project, linkname = project_id)
    patches = request.user.get_profile().todo_patches(project = project)
    filter_settings = [(DelegateFilter,
            {'delegate': request.user})]

    context = generic_list(request, project,
            'patchwork.views.user.todo_list',
            view_args = {'project_id': project.linkname},
            filter_settings = filter_settings,
            patches = patches)

    context['action_required_states'] = \
        State.objects.filter(action_required = True).all()
    return render_to_response('patchwork/todo-list.html', context)
