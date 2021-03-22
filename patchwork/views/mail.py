# Patchwork - automated patch tracking system
# Copyright (C) 2010 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import smtplib

from django.conf import settings as conf_settings
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from patchwork.forms import EmailForm
from patchwork.models import EmailConfirmation
from patchwork.models import EmailOptout


def settings(request):
    if request.method == 'POST':
        form = EmailForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            return HttpResponseRedirect(
                reverse('mail-configure', kwargs={'email': email}),
            )
    else:
        form = EmailForm()

    context = {
        'form': form,
    }

    return render(request, 'patchwork/mail-settings.html', context)


def _opt_in(request, email):
    EmailConfirmation.objects.filter(type='optin', email=email).delete()

    confirmation = EmailConfirmation(type='optin', email=email)
    confirmation.save()

    context = {'confirmation': confirmation}
    subject = render_to_string('patchwork/mails/optin-request-subject.txt')
    message = render_to_string(
        'patchwork/mails/optin-request.txt', context, request=request)

    try:
        send_mail(subject, message, conf_settings.DEFAULT_FROM_EMAIL, [email])
    except smtplib.SMTPException:
        messages.error(
            request,
            'An error occurred while submitting this request. '
            'Please contact an administrator.'
        )
        return False

    messages.success(
        request,
        'Requested opt-in to email from Patchwork. '
        'Check your email for confirmation.',
    )

    return True


def _opt_out(request, email):
    EmailConfirmation.objects.filter(type='optout', email=email).delete()

    confirmation = EmailConfirmation(type='optout', email=email)
    confirmation.save()

    context = {'confirmation': confirmation}
    subject = render_to_string('patchwork/mails/optout-request-subject.txt')
    message = render_to_string(
        'patchwork/mails/optout-request.txt', context, request=request)

    try:
        send_mail(subject, message, conf_settings.DEFAULT_FROM_EMAIL, [email])
    except smtplib.SMTPException:
        messages.error(
            request,
            'An error occurred while submitting this request. '
            'Please contact an administrator.'
        )
        return False

    messages.success(
        request,
        'Requested opt-out of email from Patchwork. '
        'Check your email for confirmation.',
    )

    return True


def configure(request, email):
    # Yes, we're kind of abusing forms here, but this is easier than doing our
    # own view-based validation
    form = EmailForm(data={'email': email})
    if not form.is_valid():
        # don't worry - Django escapes these by default
        messages.error(request, f'{email} is not a valid email address.')
        return HttpResponseRedirect(reverse(settings))

    email = form.cleaned_data['email']

    if request.method == 'POST':
        if 'optin' in request.POST:
            if _opt_in(request, email):
                return HttpResponseRedirect(reverse('project-list'))
        elif 'optout' in request.POST:
            if _opt_out(request, email):
                return HttpResponseRedirect(reverse('project-list'))
        else:
            messages.error(request, 'Invalid request.')

    is_optout = EmailOptout.objects.filter(email=email).count() > 0
    context = {
        'email': email,
        'is_optout': is_optout,
    }

    return render(request, 'patchwork/mail-configure.html', context)


def optout_confirm(request, confirmation):
    email = confirmation.email.strip().lower()
    # silently ignore duplicated optouts
    if EmailOptout.objects.filter(email=email).count() == 0:
        optout = EmailOptout(email=email)
        optout.save()

    confirmation.deactivate()

    messages.success(
        request,
        'Successfully opted out of email from Patchwork.'
    )

    return HttpResponseRedirect(reverse('project-list'))


def optin_confirm(request, confirmation):
    email = confirmation.email.strip().lower()
    EmailOptout.objects.filter(email=email).delete()

    confirmation.deactivate()

    messages.success(
        request,
        'Successfully opted into email from Patchwork.'
    )

    return HttpResponseRedirect(reverse('project-list'))
