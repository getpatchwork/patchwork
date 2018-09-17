#!/bin/sh
#
# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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
    "$PW_PYTHON" "$PATCHWORK_BASE/manage.py" parsearchive "$@"
