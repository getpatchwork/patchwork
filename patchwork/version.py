# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

import subprocess
import os


ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir)


def get_latest_version(version):
    """Returns the most recent version available.

    This is either the hard-coded version or, if using Git, the version
    per the most recent Git tag.
    """
    git_version = format_git_version(get_raw_git_version())
    str_version = format_version(version)

    return git_version or str_version


def format_version(version):
    """Format version tuple."""
    return '.'.join(['.'.join([str(x) for x in version[:3]]),
                     '-'.join([str(x) for x in version[3:]])])


def format_git_version(version):
    """Returns a version based on Git tags."""
    if '-' in version:  # after tag
        # convert version-N-githash to version.postN-githash
        return version.replace('-', '.post', 1)
    else:  # at tag
        return version


def get_raw_git_version():
    """Returns the raw git version via 'git-describe'."""
    try:
        git_version = subprocess.check_output(['git', 'describe'],
                                              cwd=ROOT_DIR)
    except (OSError, FileNotFoundError):
        return ''

    return git_version.strip().decode('utf-8')
