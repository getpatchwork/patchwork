# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import hashlib

from django.db import models
from django.utils import six


class HashField(models.CharField):

    def __init__(self, *args, **kwargs):
        self.n_bytes = len(hashlib.sha1().hexdigest())
        kwargs['max_length'] = self.n_bytes

        super(HashField, self).__init__(*args, **kwargs)

    def construct(self, value):
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')
        return hashlib.sha1(value)

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def db_type(self, connection=None):
        return 'char(%d)' % self.n_bytes
