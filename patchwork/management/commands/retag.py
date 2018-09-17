# Patchwork - automated patch tracking system
# Copyright (C) 2015 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
            if (i % 10) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()
        self.stdout.write('\ndone')
