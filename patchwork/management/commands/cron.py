# Patchwork - automated patch tracking system
# Copyright (C) 2015 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.core.management.base import BaseCommand

from patchwork.notifications import expire_notifications
from patchwork.notifications import send_notifications


class Command(BaseCommand):
    help = ('Run periodic Patchwork functions: send notifications and '
            'expire unused users')

    def handle(self, *args, **kwargs):
        errors = send_notifications()
        for (recipient, error) in errors:
            self.stderr.write("Failed sending to %s: %s" %
                              (recipient.email, error))

        expire_notifications()
