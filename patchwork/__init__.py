# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from patchwork.version import get_latest_version

VERSION = (3, 1, 0, 'alpha', 0)

__version__ = get_latest_version(VERSION)

default_app_config = 'patchwork.apps.PatchworkAppConfig'
