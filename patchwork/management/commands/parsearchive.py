# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

import logging
import mailbox
import os
import sys

import django
from django.core.management.base import BaseCommand

from patchwork import models
from patchwork.parser import parse_mail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Parse an mbox archive file and store any patches/comments found.'

    def add_arguments(self, parser):
        parser.add_argument(
            'infile',
            help='input mbox filename')
        parser.add_argument(
            '--list-id',
            help='mailing list ID. If not supplied, this will be '
            'extracted from the mail headers.')

    def handle(self, *args, **options):
        results = {
            models.Patch: 0,
            models.CoverLetter: 0,
            models.Comment: 0,
        }
        duplicates = 0
        dropped = 0
        errors = 0

        # TODO(stephenfin): Support passing via stdin
        path = args and args[0] or options['infile']
        if not os.path.exists(path):
            self.stdout.write('Invalid path: %s' % path)
            sys.exit(1)

        # assume if <infile> is a directory, then we're passing a maildir
        if os.path.isfile(path):
            mbox = mailbox.mbox(path, create=False)
        else:
            mbox = mailbox.Maildir(path, create=False)

        count = len(mbox)

        # Iterate through the mbox. This will pick up exceptions that are only
        # thrown when a broken email is found part way through. Without this
        # block, we'd get the exception thrown in enumerate(mbox) below, which
        # is harder to catch. This is due to a bug in the Python 'email'
        # library, as described here:
        #
        #   https://lists.ozlabs.org/pipermail/patchwork/2017-July/004486.html
        #
        # The alternative is converting the mbox to a list of messages, but
        # that requires holding the entire thing in memory, which is wateful.
        try:
            for m in mbox:
                pass
        except AttributeError:
            logger.warning('Broken mbox/Maildir, aborting')
            return

        logger.info('Parsing %d mails', count)
        for i, msg in enumerate(mbox):
            try:
                obj = parse_mail(msg, options['list_id'])
                if obj:
                    results[type(obj)] += 1
                else:
                    dropped += 1
            except django.db.utils.IntegrityError:
                duplicates += 1
            except ValueError:
                # TODO(stephenfin): Perhaps we should store the broken patch
                # somewhere for future reference?
                errors += 1

            if (i % 10) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()

        self.stdout.write(
            'Processed %(total)d messages -->\n'
            '  %(covers)4d cover letters\n'
            '  %(patches)4d patches\n'
            '  %(comments)4d comments\n'
            '  %(duplicates)4d duplicates\n'
            '  %(dropped)4d dropped\n'
            '  %(errors)4d errors\n'
            'Total: %(new)s new entries' % {
                'total': count,
                'covers': results[models.CoverLetter],
                'patches': results[models.Patch],
                'comments': results[models.Comment],
                'duplicates': duplicates,
                'dropped': dropped,
                'errors': errors,
                'new': count - duplicates - dropped - errors,
            })
        mbox.close()
