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

from __future__ import print_function

from optparse import OptionParser
import subprocess
import sys

def commits(options, revlist):
    cmd = ['git', 'rev-list', revlist]
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, cwd = options.repodir)

    revs = []

    for line in proc.stdout.readlines():
        revs.append(line.strip())

    return revs

def commit(options, rev):
    cmd = ['git', 'diff', '%(rev)s^..%(rev)s' % {'rev': rev}]
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, cwd = options.repodir)

    buf = proc.communicate()[0]

    return buf


def main(args):
    parser = OptionParser(usage = '%prog [options] revspec')
    parser.add_option("-p", "--project", dest = "project", action = 'store',
                  help="use project PROJECT", metavar="PROJECT")
    parser.add_option("-d", "--dir", dest = "repodir", action = 'store',
                  help="use git repo in DIR", metavar="DIR")

    (options, args) = parser.parse_args(args[1:])

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    revspec = args[0]
    revs = commits(options, revspec)

    for rev in revs:
        print(rev)
        print(commit(options, rev))


if __name__ == '__main__':
    sys.exit(main(sys.argv))

