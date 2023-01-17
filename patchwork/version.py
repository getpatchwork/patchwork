# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import subprocess
import os


ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


def get_latest_version():
    """Returns the most recent version available.

    This is either the hard-coded version or, if using Git, the version
    per the most recent Git tag.
    """
    git_version = format_git_version(get_git_version())
    str_version = format_str_version(get_str_version())

    return git_version or str_version


def format_str_version(version):
    """Format version tuple."""
    return 'v' + ''.join(
        [
            '.'.join([str(x) for x in version[:3]]),
            ''.join([str(x) for x in version[3:]]),
        ]
    )


def format_git_version(version):
    """Returns a version based on Git tags."""
    if '-' in version:  # after tag
        # convert version-N-githash to version.postN+githash
        return version.replace('-', '.post', 1).replace('-g', '+git', 1)
    else:  # at tag
        return version


def get_str_version():
    """Retrieve the version from version.txt."""
    with open(os.path.join(ROOT_DIR, 'version.txt')) as fh:
        version = fh.readline().strip()

    return version.split('.')


def get_git_version():
    """Returns the raw git version via 'git-describe'."""
    try:
        git_version = subprocess.check_output(
            ['git', 'describe'], stderr=subprocess.STDOUT, cwd=ROOT_DIR
        )
    except (OSError, subprocess.CalledProcessError):
        return ''

    return git_version.strip().decode('utf-8')
