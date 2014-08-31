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


import itertools
import datetime
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Max, Q, F
from django.db.utils import IntegrityError
from patchwork.models import Bundle, Project, BundlePatch, UserProfile, \
        PatchChangeNotification, EmailOptout, EmailConfirmation

def get_patch_ids(d, prefix = 'patch_id'):
    ids = []

    for (k, v) in d.items():
        a = k.split(':')
        if len(a) != 2:
            continue
        if a[0] != prefix:
            continue
        if not v:
            continue
        ids.append(a[1])

    return ids

class Order(object):
    order_map = {
        'date':         'date',
        'name':         'name',
        'state':        'state__ordering',
        'submitter':    'submitter__name',
        'delegate':     'delegate__username',
    }
    default_order = ('date', True)

    def __init__(self, str = None, editable = False):
        self.reversed = False
        self.editable = editable
        (self.order, self.reversed) = self.default_order

        if self.editable:
            return

        if str is None or str == '':
            return

        reversed = False
        if str[0] == '-':
            str = str[1:]
            reversed = True

        if str not in self.order_map.keys():
            return

        self.order = str
        self.reversed = reversed

    def __str__(self):
        str = self.order
        if self.reversed:
            str = '-' + str
        return str

    def name(self):
        return self.order

    def reversed_name(self):
        if self.reversed:
            return self.order
        else:
            return '-' + self.order

    def updown(self):
        if self.reversed:
            return 'up'
        return 'down'

    def apply(self, qs):
        q = self.order_map[self.order]
        if self.reversed:
            q = '-' + q

        orders = [q]

        # if we're using a non-default order, add the default as a secondary
        # ordering. We reverse the default if the primary is reversed.
        (default_name, default_reverse) = self.default_order
        if self.order != default_name:
            q = self.order_map[default_name]
            if self.reversed ^ default_reverse:
                q = '-' + q
            orders.append(q)

        return qs.order_by(*orders)

bundle_actions = ['create', 'add', 'remove']
def set_bundle(user, project, action, data, patches, context):
    # set up the bundle
    bundle = None
    if action == 'create':
        bundle_name = data['bundle_name'].strip()
        if '/' in bundle_name:
            return ['Bundle names can\'t contain slashes']

        if not bundle_name:
            return ['No bundle name was specified']

        if Bundle.objects.filter(owner = user, name = bundle_name).count() > 0:
            return ['You already have a bundle called "%s"' % bundle_name]

        bundle = Bundle(owner = user, project = project,
                name = bundle_name)
        bundle.save()
        context.add_message("Bundle %s created" % bundle.name)

    elif action =='add':
        bundle = get_object_or_404(Bundle, id = data['bundle_id'])

    elif action =='remove':
        bundle = get_object_or_404(Bundle, id = data['removed_bundle_id'])

    if not bundle:
        return ['no such bundle']

    for patch in patches:
        if action == 'create' or action == 'add':
            bundlepatch_count = BundlePatch.objects.filter(bundle = bundle,
                        patch = patch).count()
            if bundlepatch_count == 0:
                bundle.append_patch(patch)
                context.add_message("Patch '%s' added to bundle %s" % \
                        (patch.name, bundle.name))
            else:
                context.add_message("Patch '%s' already in bundle %s" % \
                        (patch.name, bundle.name))

        elif action == 'remove':
            try:
                bp = BundlePatch.objects.get(bundle = bundle, patch = patch)
                bp.delete()
                context.add_message("Patch '%s' removed from bundle %s\n" % \
                        (patch.name, bundle.name))
            except Exception:
                pass

    bundle.save()

    return []

def send_notifications():
    date_limit = datetime.datetime.now() - \
                     datetime.timedelta(minutes =
                                settings.NOTIFICATION_DELAY_MINUTES)

    # This gets funky: we want to filter out any notifications that should
    # be grouped with other notifications that aren't ready to go out yet. To
    # do that, we join back onto PatchChangeNotification (PCN -> Patch ->
    # Person -> Patch -> max(PCN.last_modified)), filtering out any maxima
    # that are with the date_limit.
    qs = PatchChangeNotification.objects \
            .annotate(m = Max('patch__submitter__patch__patchchangenotification'
                        '__last_modified')) \
                .filter(m__lt = date_limit)

    groups = itertools.groupby(qs.order_by('patch__submitter'),
                               lambda n: n.patch.submitter)

    errors = []

    for (recipient, notifications) in groups:
        notifications = list(notifications)
        projects = set([ n.patch.project.linkname for n in notifications ])

        def delete_notifications():
            pks = [ n.pk for n in notifications ]
            PatchChangeNotification.objects.filter(pk__in = pks).delete()

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

        message = EmailMessage(subject = subject, body = content,
                               from_email = settings.NOTIFICATION_FROM_EMAIL,
                               to = [recipient.email],
                               headers = {'Precedence': 'bulk'})

        try:
            message.send()
        except ex:
            errors.append((recipient, ex))
            continue

        delete_notifications()

    return errors

def do_expiry():
    # expire any pending confirmations
    q = (Q(date__lt = datetime.datetime.now() - EmailConfirmation.validity) |
            Q(active = False))
    EmailConfirmation.objects.filter(q).delete()

    # expire inactive users with no pending confirmation
    pending_confs = EmailConfirmation.objects.values('user')
    users = User.objects.filter(
                is_active = False,
                last_login = F('date_joined')
            ).exclude(
                id__in = pending_confs
            )

    # delete users
    users.delete()



