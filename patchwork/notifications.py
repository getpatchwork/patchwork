# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import itertools
import smtplib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.db.models import Count
from django.db.models import Q
from django.template.loader import render_to_string

from patchwork.models import EmailConfirmation
from patchwork.models import EmailOptout
from patchwork.models import PatchChangeNotification


def send_notifications():
    date_limit = datetime.datetime.utcnow() - datetime.timedelta(
        minutes=settings.NOTIFICATION_DELAY_MINUTES)

    # We delay sending notifications to a user if they have other
    # notifications that are still in the "pending" state. To do this,
    # we compare the total number of patch change notifications queued
    # for each user against the number of "ready" notifications.
    qs = PatchChangeNotification.objects.all()
    qs2 = PatchChangeNotification.objects\
        .filter(last_modified__lt=date_limit)\
        .values('patch__submitter')\
        .annotate(count=Count('patch__submitter'))
    qs2 = {elem['patch__submitter']: elem['count'] for elem in qs2}

    groups = itertools.groupby(qs.order_by('patch__submitter'),
                               lambda n: n.patch.submitter)

    errors = []

    for (recipient, notifications) in groups:
        notifications = list(notifications)

        if recipient.id not in qs2 or qs2[recipient.id] < len(notifications):
            continue

        projects = set([n.patch.project.linkname for n in notifications])

        def delete_notifications():
            pks = [n.pk for n in notifications]
            PatchChangeNotification.objects.filter(pk__in=pks).delete()

        if EmailOptout.is_optout(recipient.email):
            delete_notifications()
            continue

        context = {
            'site': Site.objects.get_current(),
            'notifications': notifications,
            'projects': projects,
        }

        subject = render_to_string(
            'patchwork/mails/patch-change-notification-subject.txt',
            context).strip()
        content = render_to_string(
            'patchwork/mails/patch-change-notification.txt',
            context)

        message = EmailMessage(subject=subject, body=content,
                               from_email=settings.NOTIFICATION_FROM_EMAIL,
                               to=[recipient.email],
                               headers={'Precedence': 'bulk'})

        try:
            message.send()
        except smtplib.SMTPException as ex:
            errors.append((recipient, ex))
            continue

        delete_notifications()

    return errors


def expire_notifications():
    """Expire any pending confirmations.

    Users whose registration confirmation has expired are removed.
    """
    # expire any invalid confirmations
    q = (Q(date__lt=datetime.datetime.utcnow() - EmailConfirmation.validity) |
         Q(active=False))
    EmailConfirmation.objects.filter(q).delete()

    # remove inactive users with no pending confirmation
    pending_confs = (EmailConfirmation.objects
                     .filter(user__isnull=False).values('user'))
    users = User.objects.filter(is_active=False).exclude(id__in=pending_confs)

    # delete users
    users.delete()
