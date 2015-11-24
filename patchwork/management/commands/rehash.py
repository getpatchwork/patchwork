#!/usr/bin/env python
#
# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
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

from patchwork.models import Patch


class Command(BaseCommand):
    help = 'Update the hashes on existing patches'
    args = '[<patch_id>...]'

    def handle(self, *args, **options):
        query = Patch.objects

        if args:
            query = query.filter(id_in=args)
        else:
            query = query.all()

        count = query.count()

        for i, patch in enumerate(query.iterator()):
            patch.hash = None
            patch.save()
            if (i % 10) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()
        self.stdout.write('\ndone')
