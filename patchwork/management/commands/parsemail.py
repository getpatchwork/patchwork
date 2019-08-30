# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email
import logging
import sys

from django.core.management import base

from patchwork.parser import parse_mail
from patchwork.parser import DuplicateMailError

logger = logging.getLogger(__name__)


class Command(base.BaseCommand):
    help = 'Parse an mbox file and store any patch/comment found.'

    def add_arguments(self, parser):
        parser.add_argument(
            'infile',
            nargs='?',
            type=str,
            default=None,
            help='input mbox file (a filename or stdin)')
        parser.add_argument(
            '--list-id',
            help='mailing list ID. If not supplied, this will be '
            'extracted from the mail headers.')

    def handle(self, *args, **options):
        infile = args[0] if args else options['infile']

        try:
            if infile:
                logger.info('Parsing mail loaded by filename')
                with open(infile, 'rb') as file_:
                    mail = email.message_from_binary_file(file_)
            else:
                logger.info('Parsing mail loaded from stdin')
                mail = email.message_from_binary_file(sys.stdin.buffer)
        except AttributeError:
            logger.warning("Broken email ignored")
            return

        # it's important to get exit codes correct here. The key is to allow
        # proper separation of real errors vs expected 'failures'.
        #
        # patch/comment parsed:        0
        # no parseable content found:  0
        # duplicate messages:          0
        # db integrity/other db error: 1
        # broken email (ValueError):   1 (this could be noisy, if it's an issue
        #                                 we could use a different return code)
        try:
            result = parse_mail(mail, options['list_id'])
            if result is None:
                logger.warning('Nothing added to database')
        except DuplicateMailError as exc:
            logger.warning('Duplicate mail for message ID %s', exc.msgid)
        except (ValueError, Exception) as exc:
            logger.exception('Error when parsing incoming email: %s',
                             repr(exc),
                             extra={'mail': mail.as_string()})
            sys.exit(1)
