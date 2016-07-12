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

import re

from django.utils.six.moves import map


_hunk_re = re.compile('^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
_filename_re = re.compile('^(---|\+\+\+) (\S+)')


def parse_patch(content):
    """Split a mail's contents into a diff and comment.

    This is a state machine that takes a patch, generally in UNIX mbox
    format, and splits it into the component comments and diff.

    Args:
        patch: The patch to be split

    Returns:
        A tuple containing the diff and comment. Either one or both of
        these can be empty.

    Raises:
        Exception: The state machine transitioned to an invalid state.
    """
    patchbuf = ''
    commentbuf = ''
    buf = ''

    # state specified the line we just saw, and what to expect next
    state = 0
    # 0: text
    # 1: suspected patch header (diff, ====, Index:)
    # 2: patch header line 1 (---)
    # 3: patch header line 2 (+++)
    # 4: patch hunk header line (@@ line)
    # 5: patch hunk content
    # 6: patch meta header (rename from/rename to)
    #
    # valid transitions:
    #  0 -> 1 (diff, ===, Index:)
    #  0 -> 2 (---)
    #  1 -> 2 (---)
    #  2 -> 3 (+++)
    #  3 -> 4 (@@ line)
    #  4 -> 5 (patch content)
    #  5 -> 1 (run out of lines from @@-specifed count)
    #  1 -> 6 (rename from / rename to)
    #  6 -> 2 (---)
    #  6 -> 1 (other text)
    #
    # Suspected patch header is stored into buf, and appended to
    # patchbuf if we find a following hunk. Otherwise, append to
    # comment after parsing.

    # line counts while parsing a patch hunk
    lc = (0, 0)
    hunk = 0

    for line in content.split('\n'):
        line += '\n'

        if state == 0:
            if line.startswith('diff ') or line.startswith('===') \
                    or line.startswith('Index: '):
                state = 1
                buf += line
            elif line.startswith('--- '):
                state = 2
                buf += line
            else:
                commentbuf += line
        elif state == 1:
            buf += line
            if line.startswith('--- '):
                state = 2

            if line.startswith(('rename from ', 'rename to ')):
                state = 6
        elif state == 2:
            if line.startswith('+++ '):
                state = 3
                buf += line
            elif hunk:
                state = 1
                buf += line
            else:
                state = 0
                commentbuf += buf + line
                buf = ''
        elif state == 3:
            match = _hunk_re.match(line)
            if match:
                def fn(x):
                    if not x:
                        return 1
                    return int(x)

                lc = list(map(fn, match.groups()))

                state = 4
                patchbuf += buf + line
                buf = ''
            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2
            elif hunk and line.startswith('\ No newline at end of file'):
                # If we had a hunk and now we see this, it's part of the patch,
                # and we're still expecting another @@ line.
                patchbuf += line
            elif hunk:
                state = 1
                buf += line
            else:
                state = 0
                commentbuf += buf + line
                buf = ''
        elif state == 4 or state == 5:
            if line.startswith('-'):
                lc[0] -= 1
            elif line.startswith('+'):
                lc[1] -= 1
            elif line.startswith('\ No newline at end of file'):
                # Special case: Not included as part of the hunk's line count
                pass
            else:
                lc[0] -= 1
                lc[1] -= 1

            patchbuf += line

            if lc[0] <= 0 and lc[1] <= 0:
                state = 3
                hunk += 1
            else:
                state = 5
        elif state == 6:
            if line.startswith(('rename to ', 'rename from ')):
                patchbuf += buf + line
                buf = ''
            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2
            else:
                buf += line
                state = 1
        else:
            raise Exception("Unknown state %d! (line '%s')" % (state, line))

    commentbuf += buf

    if patchbuf == '':
        patchbuf = None

    if commentbuf == '':
        commentbuf = None

    return patchbuf, commentbuf


def find_filenames(diff):
    """Find files changes in a given diff."""
    # normalise spaces
    diff = diff.replace('\r', '')
    diff = diff.strip() + '\n'

    filenames = {}

    for line in diff.split('\n'):
        if len(line) <= 0:
            continue

        filename_match = _filename_re.match(line)
        if not filename_match:
            continue

        filename = filename_match.group(2)
        if filename.startswith('/dev/null'):
            continue

        filename = '/'.join(filename.split('/')[1:])
        filenames[filename] = True

    filenames = sorted(filenames.keys())

    return filenames
