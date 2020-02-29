# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import mailbox
import os
import sys

from django.core.management.base import BaseCommand

from patchwork import models
from patchwork.parser import parse_mail
from patchwork.parser import DuplicateMailError

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
            models.Cover: 0,
            models.PatchComment: 0,
            models.CoverComment: 0,
        }
        duplicates = 0
        dropped = 0
        errors = 0

        verbosity = int(options['verbosity'])
        if not verbosity:
            level = logging.CRITICAL
        elif verbosity == 1:
            level = logging.ERROR
        elif verbosity == 2:
            level = logging.INFO
        else:  # verbosity == 3
            level = logging.DEBUG

        if level:
            logger.setLevel(level)
            logging.getLogger('patchwork.parser').setLevel(level)

        # TODO(stephenfin): Support passing via stdin
        path = args and args[0] or options['infile']
        if not os.path.exists(path):
            logger.error('Invalid path: %s', path)
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
            logger.error('Broken mbox/Maildir, aborting')
            return

        logger.info('Parsing %d mails', count)
        for i, msg in enumerate(mbox):
            try:
                obj = parse_mail(msg, options['list_id'])
                if obj:
                    results[type(obj)] += 1
                else:
                    dropped += 1
            except DuplicateMailError as exc:
                duplicates += 1
                logger.warning('Duplicate mail for message ID %s', exc.msgid)
            except (ValueError, Exception) as exc:
                errors += 1
                logger.warning('Invalid mail: %s', repr(exc))

            if verbosity < 3 and (i % 10) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()

        mbox.close()

        if not verbosity:
            return

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
                'covers': results[models.Cover],
                'patches': results[models.Patch],
                'comments': (
                    results[models.CoverComment] + results[models.PatchComment]
                ),
                'duplicates': duplicates,
                'dropped': dropped,
                'errors': errors,
                'new': count - duplicates - dropped - errors,
            })
