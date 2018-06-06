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

BIN_DIR=$(dirname "$0")
PATCHWORK_BASE=$(readlink -e "$BIN_DIR/../..")

if [ -z "$PW_PYTHON" ]; then
    PW_PYTHON=python
fi

if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    DJANGO_SETTINGS_MODULE=patchwork.settings.production
fi

PYTHONPATH="${PATCHWORK_BASE}:${PATCHWORK_BASE}/lib/python:$PYTHONPATH" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$PW_PYTHON" "$PATCHWORK_BASE/manage.py" parsemail "$@"

# NOTE(stephenfin): We must return 0 here. When parsemail is used as a
# delivery command from a mail server like postfix (as it is intended
# to be), a non-zero exit code will cause a bounce message to be
# returned to the user. We don't want to do that for a parse error, so
# always return 0. For more information, refer to
# https://patchwork.ozlabs.org/patch/602248/
exit 0
