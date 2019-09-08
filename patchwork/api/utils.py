# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from distutils.version import StrictVersion


def has_version(request, version):
    if not request.version:
        # without version information, we have to assume the latest
        return True

    return StrictVersion(request.version) >= StrictVersion(version)
