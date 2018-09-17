# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import SimpleTestCase

from patchwork import fields


class TestHashField(SimpleTestCase):

    def test_n_bytes(self):
        """Sanity check the hashing algorithm.

        Changing this can change our database schema.
        """
        field = fields.HashField()
        self.assertEqual(field.n_bytes, 40)
