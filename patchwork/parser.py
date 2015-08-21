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


import hashlib
import re
from collections import Counter

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


    for line in text.split('\n'):
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

            if line.startswith('rename from ') or line.startswith('rename to '):
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

                lc = map(fn, match.groups())

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
            if line.startswith('rename to ') or line.startswith('rename from '):
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

    return (patchbuf, commentbuf)

def hash_patch(str):
    # normalise spaces
    str = str.replace('\r', '')
    str = str.strip() + '\n'

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
            # remove line numbers, but leave line counts
            def fn(x):
                if not x:
                    return 1
                return int(x)
            line_nos = map(fn, hunk_match.groups())
            line = '@@ -%d +%d @@' % tuple(line_nos)

        elif line[0] in prefixes:
            # if we have a +, - or context line, leave as-is
            pass

        else:
            # other lines are ignored
            continue

        hash.update(line.encode('utf-8') + '\n')

    return hash

def extract_tags(content, tags):
    counts = Counter()

    for tag in tags:
        regex = re.compile(tag.pattern, re.MULTILINE | re.IGNORECASE)
        counts[tag] = len(regex.findall(content))

    return counts

def main(args):
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-p', '--patch', action = 'store_true',
            dest = 'print_patch', help = 'print parsed patch')
    parser.add_option('-c', '--comment', action = 'store_true',
            dest = 'print_comment', help = 'print parsed comment')
    parser.add_option('-#', '--hash', action = 'store_true',
            dest = 'print_hash', help = 'print patch hash')

    (options, args) = parser.parse_args()

    # decode from (assumed) UTF-8
    content = sys.stdin.read().decode('utf-8')

    (patch, comment) = parse_patch(content)

    if options.print_hash and patch:
        print hash_patch(patch).hexdigest()

    if options.print_patch and patch:
        print "Patch: ------\n" + patch

    if options.print_comment and comment:
        print "Comment: ----\n" + comment

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
