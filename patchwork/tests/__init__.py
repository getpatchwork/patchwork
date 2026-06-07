# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import warnings

TEST_MAIL_DIR = os.path.join(os.path.dirname(__file__), 'data', 'mail')
TEST_PATCH_DIR = os.path.join(os.path.dirname(__file__), 'data', 'patches')
TEST_FUZZ_DIR = os.path.join(os.path.dirname(__file__), 'data', 'fuzz')
TEST_SERIES_DIR = os.path.join(os.path.dirname(__file__), 'data', 'series')

# configure warnings

warnings.simplefilter('once', DeprecationWarning)
