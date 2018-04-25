# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
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

from django.conf import settings as conf_settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string

from patchwork.compat import reverse
from patchwork.forms import EmailForm
from patchwork.models import EmailConfirmation
from patchwork.models import EmailOptout


def settings(request):
    if request.method == 'POST':
        form = EmailForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            is_optout = EmailOptout.objects.filter(email=email).count() > 0
            context = {
                'email': email,
                'is_optout': is_optout,
            }
            return render(request, 'patchwork/mail-settings.html', context)
    else:
        form = EmailForm()

    context = {
        'form': form,
    }

    return render(request, 'patchwork/mail-form.html', context)


def optout_confirm(request, conf):
    email = conf.email.strip().lower()
    # silently ignore duplicated optouts
    if EmailOptout.objects.filter(email=email).count() == 0:
        optout = EmailOptout(email=email)
        optout.save()

    conf.deactivate()

    context = {
        'email': conf.email,
    }

    return render(request, 'patchwork/optout.html', context)


def optin_confirm(request, conf):
    email = conf.email.strip().lower()
    EmailOptout.objects.filter(email=email).delete()

    conf.deactivate()

    context = {
        'email': conf.email,
    }

    return render(request, 'patchwork/optin.html', context)


def _optinout(request, action, description):
    context = {}
    mail_template = 'patchwork/%s-request.mail' % action
    html_template = 'patchwork/%s-request.html' % action

    if request.method != 'POST':
        return HttpResponseRedirect(reverse(settings))

    form = EmailForm(data=request.POST)
    if not form.is_valid():
        context['error'] = ('There was an error in the %s form. Please '
                            'review the form and re-submit.' % description)
        context['form'] = form
        return render(request, html_template, context)

    email = form.cleaned_data['email']
    if action == 'optin' and \
            EmailOptout.objects.filter(email=email).count() == 0:
        context['error'] = ("The email address %s is not on the patchwork "
                            "opt-out list, so you don't need to opt back in" %
                            email)
        context['form'] = form
        return render(request, html_template, context)

    conf = EmailConfirmation(type=action, email=email)
    conf.save()

    context['confirmation'] = conf
    mail = render_to_string(mail_template, context, request=request)

    try:
        send_mail('Patchwork %s confirmation' % description, mail,
                  conf_settings.DEFAULT_FROM_EMAIL, [email])
        context['email_sent'] = True
    except smtplib.SMTPException:
        context['error'] = ('An error occurred during confirmation . '
                            'Please try again later.')
        context['admins'] = conf_settings.ADMINS

    return render(request, html_template, context)


def optout(request):
    return _optinout(request, 'optout', 'opt-out')


def optin(request):
    return _optinout(request, 'optin', 'opt-in')
