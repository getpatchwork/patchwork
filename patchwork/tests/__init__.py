# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import warnings

TEST_MAIL_DIR = os.path.join(os.path.dirname(__file__), 'mail')
TEST_PATCH_DIR = os.path.join(os.path.dirname(__file__), 'patches')
TEST_FUZZ_DIR = os.path.join(os.path.dirname(__file__), 'fuzztests')

# configure warnings

warnings.simplefilter('once', DeprecationWarning)

# TODO: Remove this once [1] merges and is released
# [1] https://github.com/p1c2u/openapi-core/pull/395
warnings.filterwarnings(
    'ignore',
    message=(
        'The distutils package is deprecated and slated for removal in Python '
        '3.12. Use setuptools or check PEP 632 for potential alternatives'
    ),
    module='openapi_core',
    category=DeprecationWarning,
)
