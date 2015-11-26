# Patchwork - automated patch tracking system
# Copyright (C) 2015 Jeremy Kerr <jk@ozlabs.org>
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

from django.core.management.base import BaseCommand

from patchwork.utils import send_notifications, do_expiry


class Command(BaseCommand):
    help = ('Run periodic patchwork functions: send notifications and '
            'expire unused users')

    def handle(self, *args, **kwargs):
        errors = send_notifications()
        for (recipient, error) in errors:
            self.stderr.write("Failed sending to %s: %s" %
                              (recipient.email, error))

        do_expiry()
