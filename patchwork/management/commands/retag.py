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
from patchwork.models import Patch


class Command(BaseCommand):
    help = 'Update the tag (Ack/Review/Test) counts on existing patches'
    args = '[<patch_id>...]'

    def handle(self, *args, **options):
        query = Patch.objects

        if args:
            query = query.filter(id__in=args)
        else:
            query = query.all()

        count = query.count()

        for i, patch in enumerate(query.iterator()):
            patch.refresh_tag_counts()
            if (i % 10) == 0 or i == count:
                self.stdout.write('%06d/%06d\r' % (i, count))
                self.stdout.flush()
        self.stderr.write('\ndone\n')
