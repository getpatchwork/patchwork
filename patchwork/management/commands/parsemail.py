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

import email
import logging
from optparse import make_option
import sys

import django
from django.core.management import base
from django.utils import six

from patchwork.parser import parse_mail

logger = logging.getLogger(__name__)


class Command(base.BaseCommand):
    help = 'Parse an mbox file and store any patch/comment found.'

    if django.VERSION < (1, 8):
        args = '<infile>'
        option_list = base.BaseCommand.option_list + (
            make_option(
                '--list-id',
                help='mailing list ID. If not supplied, this will be '
                'extracted from the mail headers.'),
        )
    else:
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
                if six.PY3:
                    with open(infile, 'rb') as file_:
                        mail = email.message_from_binary_file(file_)
                else:
                    with open(infile) as file_:
                        mail = email.message_from_file(file_)
            else:
                logger.info('Parsing mail loaded from stdin')
                if six.PY3:
                    mail = email.message_from_binary_file(sys.stdin.buffer)
                else:
                    mail = email.message_from_file(sys.stdin)
        except AttributeError:
            logger.warning("Broken email ignored")
            return

        try:
            result = parse_mail(mail, options['list_id'])
            if result:
                sys.exit(0)
            logger.warning('Failed to parse mail')
            sys.exit(1)
        except Exception:
            logger.exception('Error when parsing incoming email',
                             extra={'mail': mail.as_string()})
