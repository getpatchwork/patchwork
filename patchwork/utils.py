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

import datetime
import itertools

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.db.models import Max, Q, F
from django.template.loader import render_to_string

from patchwork.models import (PatchChangeNotification, EmailOptout,
                              EmailConfirmation)


def send_notifications():
    date_limit = datetime.datetime.now() - datetime.timedelta(
        minutes=settings.NOTIFICATION_DELAY_MINUTES)

    # This gets funky: we want to filter out any notifications that should
    # be grouped with other notifications that aren't ready to go out yet. To
    # do that, we join back onto PatchChangeNotification (PCN -> Patch ->
    # Person -> Patch -> max(PCN.last_modified)), filtering out any maxima
    # that are with the date_limit.
    qs = PatchChangeNotification.objects.annotate(
        m=Max('patch__submitter__patch__patchchangenotification'
              '__last_modified')).filter(m__lt=date_limit)

    groups = itertools.groupby(qs.order_by('patch__submitter'),
                               lambda n: n.patch.submitter)

    errors = []

    for (recipient, notifications) in groups:
        notifications = list(notifications)
        projects = set([n.patch.project.linkname for n in notifications])

        def delete_notifications():
            pks = [n.pk for n in notifications]
            PatchChangeNotification.objects.filter(pk__in=pks).delete()

        if EmailOptout.is_optout(recipient.email):
            delete_notifications()
            continue

        context = {
            'site': Site.objects.get_current(),
            'person': recipient,
            'notifications': notifications,
            'projects': projects,
        }

        subject = render_to_string(
            'patchwork/patch-change-notification-subject.text',
            context).strip()
        content = render_to_string('patchwork/patch-change-notification.mail',
                                   context)

        message = EmailMessage(subject=subject, body=content,
                               from_email=settings.NOTIFICATION_FROM_EMAIL,
                               to=[recipient.email],
                               headers={'Precedence': 'bulk'})

        try:
            message.send()
        except Exception as ex:
            errors.append((recipient, ex))
            continue

        delete_notifications()

    return errors


def do_expiry():
    # expire any pending confirmations
    q = (Q(date__lt=datetime.datetime.now() - EmailConfirmation.validity) |
         Q(active=False))
    EmailConfirmation.objects.filter(q).delete()

    # expire inactive users with no pending confirmation
    pending_confs = EmailConfirmation.objects.values('user')
    users = User.objects.filter(is_active=False,
                                last_login=F('date_joined')).exclude(
                                    id__in=pending_confs)

    # delete users
    users.delete()
