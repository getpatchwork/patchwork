# Patchwork - automated patch tracking system
# Copyright (C) 2022 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re
import unittest

from patchwork import version

from django import test


class TestVersion(test.TestCase):
    @unittest.skipIf(
        version.get_git_version() == '',
        "this doesn't appear to be a git repo so we can't run git-based tests",
    )
    def test_validate_version(self):
        str_version = version.get_str_version()
        git_version = version.get_git_version()

        str_re = r'v\d\.\d\.\d(([ab]|rc)\d+)?'  # v1.2.3a0
        git_re = r'v\d\.\d\.\d(\.post\d+\+\w+)?'  # v1.2.3.post1+abc123

        str_match = re.match(str_re, version.format_str_version(str_version))
        git_match = re.match(git_re, version.format_git_version(git_version))

        # both should match a specific pattern at a minimum
        self.assertIsNotNone(str_match)
        self.assertIsNotNone(git_match)

        # if the tag is missing from one, it should be missing from the other
        # (and vice versa)
        self.assertEqual(
            bool(str_match.group(1)),
            bool(git_match.group(1)),
            f'mismatch between git and version.txt post-release metadata: '
            f'git={git_match.group(1)!r}, version.txt={str_match.group(1)!r}',
        )
