#!/bin/sh
#
# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
