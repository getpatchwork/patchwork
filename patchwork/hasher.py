#!/usr/bin/env python
#
# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Hash generation for diffs."""

import hashlib
import re
import sys

HUNK_RE = re.compile(r'^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
FILENAME_RE = re.compile(r'^(---|\+\+\+) (\S+)')


def hash_diff(diff):
    """Generate a hash from a diff."""

    # normalise spaces
    diff = diff.replace('\r', '')
    diff = diff.strip() + '\n'

    prefixes = ['-', '+', ' ']
    hashed = hashlib.sha1()

    for line in diff.split('\n'):
        if len(line) <= 0:
            continue

        hunk_match = HUNK_RE.match(line)
        filename_match = FILENAME_RE.match(line)

        if filename_match:
            # normalise -p1 top-directories
            if filename_match.group(1) == '---':
                filename = 'a/'
            else:
                filename = 'b/'
            filename += '/'.join(filename_match.group(2).split('/')[1:])

            line = filename_match.group(1) + ' ' + filename
        elif hunk_match:
            # remove line numbers, but leave line counts
            def fn(x):
                if not x:
                    return 1
                return int(x)
            line_nos = list(map(fn, hunk_match.groups()))
            line = '@@ -%d +%d @@' % tuple(line_nos)
        elif line[0] in prefixes:
            # if we have a +, - or context line, leave as-is
            pass
        else:
            # other lines are ignored
            continue

        hashed.update((line + '\n').encode('utf-8'))

    return hashed.hexdigest()


def main(args):
    """Hash a diff provided by stdin.

    This is required by scripts found in /tools
    """
    print(hash_diff('\n'.join(sys.stdin.readlines())))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
