#!/usr/bin/env python
#
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

from __future__ import absolute_import

import argparse
from email import message_from_file
import logging
import sys

import django
from django.conf import settings
from django.utils.log import AdminEmailHandler

from patchwork.parser import parse_mail

LOGGER = logging.getLogger(__name__)

VERBOSITY_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


extra_error_message = '''
== Mail

%(mail)s


== Traceback

'''


def setup_error_handler():
    """Configure error handler.

    Ensure emails are send to settings.ADMINS when errors are
    encountered.
    """
    if settings.DEBUG:
        return

    mail_handler = AdminEmailHandler()
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(extra_error_message))

    logger = logging.getLogger('patchwork')
    logger.addHandler(mail_handler)

    return logger


def main(args):
    django.setup()
    logger = setup_error_handler()
    parser = argparse.ArgumentParser()

    def list_logging_levels():
        """Give a summary of all available logging levels."""
        return sorted(list(VERBOSITY_LEVELS.keys()),
                      key=lambda x: VERBOSITY_LEVELS[x])

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help='input mbox file (a filename '
                        'or stdin)')

    group = parser.add_argument_group('Mail parsing configuration')
    group.add_argument('--list-id', help='mailing list ID. If not supplied '
                       'this will be extracted from the mail headers.')
    group.add_argument('--verbosity', choices=list_logging_levels(),
                       help='debug level', default='info')

    args = vars(parser.parse_args())

    logging.basicConfig(level=VERBOSITY_LEVELS[args['verbosity']])

    mail = message_from_file(args['infile'])
    try:
        result = parse_mail(mail, args['list_id'])
        if result:
            return 0
        return 1
    except:
        if logger:
            logger.exception('Error when parsing incoming email', extra={
                'mail': mail.as_string(),
            })
        raise

if __name__ == '__main__':
    sys.exit(main(sys.argv))
