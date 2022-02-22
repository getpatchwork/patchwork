# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later


def _parse_version(version):
    return version.split('.')


def has_version(request, version):
    if not request.version:
        # without version information, we have to assume the latest
        return True

    return _parse_version(request.version) >= _parse_version(version)
