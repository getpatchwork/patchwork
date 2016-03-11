#!/usr/bin/env python
#
# Patchwork - automated patch tracking system
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

"""Utility to parse an mbox archive file."""

from __future__ import absolute_import

import argparse
import logging
import mailbox

import django

from patchwork.bin import parsemail

LOGGER = logging.getLogger(__name__)

VERBOSITY_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def parse_mbox(path, list_id):
    mbox = mailbox.mbox(path)
    duplicates = 0
    for msg in mbox:
        try:
            parsemail.parse_mail(msg, list_id)
        except django.db.utils.IntegrityError:
            duplicates += 1
    LOGGER.info('Processed %d messages, %d duplicates',
                len(mbox), duplicates)


def main():
    django.setup()
    parser = argparse.ArgumentParser(description=__doc__)

    def list_logging_levels():
        """Give a summary of all available logging levels."""
        return sorted(VERBOSITY_LEVELS.keys(),
                      key=lambda x: VERBOSITY_LEVELS[x])

    parser.add_argument('inpath', help='input mbox filename')

    group = parser.add_argument_group('Mail parsing configuration')
    group.add_argument('--list-id', help='mailing list ID. If not supplied '
                       'this will be extracted from the mail headers.')
    group.add_argument('--verbosity', choices=list_logging_levels(),
                       help='debug level', default=logging.INFO)

    args = vars(parser.parse_args())

    logging.basicConfig(level=VERBOSITY_LEVELS[args['verbosity']])

    parse_mbox(args['inpath'], args['list_id'])

if __name__ == '__main__':
    main()
