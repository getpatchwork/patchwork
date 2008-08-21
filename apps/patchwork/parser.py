#!/usr/bin/python
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
import hashlib

_hunk_re = re.compile('^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
_filename_re = re.compile('^(---|\+\+\+) (\S+)')

def parse_patch(text):
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
    #
    # valid transitions:
    #  0 -> 1 (diff, ===, Index:)
    #  0 -> 2 (---)
    #  1 -> 2 (---)
    #  2 -> 3 (+++)
    #  3 -> 4 (@@ line)
    #  4 -> 5 (patch content)
    #  5 -> 1 (run out of lines from @@-specifed count)
    #
    # Suspected patch header is stored into buf, and appended to
    # patchbuf if we find a following hunk. Otherwise, append to
    # comment after parsing.

    # line counts while parsing a patch hunk
    lc = (0, 0)
    hunk = 0


    for line in text.split('\n'):
        line += '\n'

        if state == 0:
            if line.startswith('diff') or line.startswith('===') \
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

                lc = map(fn, match.groups())

                state = 4
                patchbuf += buf + line
                buf = ''

            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2

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
            else:
                lc[0] -= 1
                lc[1] -= 1

            patchbuf += line

            if lc[0] <= 0 and lc[1] <= 0:
                state = 3
                hunk += 1
            else:
                state = 5

        else:
            raise Exception("Unknown state %d! (line '%s')" % (state, line))

    commentbuf += buf

    if patchbuf == '':
        patchbuf = None

    if commentbuf == '':
        commentbuf = None

    return (patchbuf, commentbuf)

def patch_hash(str):
    str = str.replace('\r', '')
    str = str.strip() + '\n'
    lines = str.split('\n')

    prefixes = ['-', '+', ' ']
    hash = hashlib.sha1()

    for line in str.split('\n'):

        if len(line) <= 0:
            continue

	hunk_match = _hunk_re.match(line)
	filename_match = _filename_re.match(line)

        if filename_match:
            # normalise -p1 top-directories
            if filename_match.group(1) == '---':
                filename = 'a/'
            else:
                filename = 'b/'
            filename += '/'.join(filename_match.group(2).split('/')[1:])

            line = filename_match.group(1) + ' ' + filename

            
	elif hunk_match:
            # remove line numbers
            def fn(x):
                if not x:
                    return 1
                return int(x)
            line_nos = map(fn, hunk_match.groups())
            line = '@@ -%d +%d @@' % tuple(line_nos)

        elif line[0] in prefixes:
            pass

        else:
            continue

        hash.update(line + '\n')

if __name__ == '__main__':
    import sys
#    (patch, comment) = parse_patch(sys.stdin.read())
#    if patch:
#        print "Patch: ------\n" + patch
#    if comment:
#        print "Comment: ----\n" + comment
    normalise_patch_content(sys.stdin.read())
