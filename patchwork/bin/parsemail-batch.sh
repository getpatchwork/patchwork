#!/bin/sh
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

PATCHWORK_BINDIR=`dirname $0`

if [ $# -lt 1 ]
then
	echo "usage: $0 <dir> [options]" >&2
	exit 1
fi

mail_dir="$1"

echo "dir: $mail_dir"

if [ ! -d "$mail_dir" ]
then
	echo "$mail_dir should be a directory"? >&2
	exit 1
fi

shift

ls -1rt "$mail_dir" |
while read line;
do
	echo $line
	$PATCHWORK_BINDIR/parsemail.sh $@ < "$mail_dir/$line"
done
