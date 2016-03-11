# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
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

from __future__ import absolute_import

import hashlib

import django
from django.db import models
from django.utils import six


if django.VERSION < (1, 8):
    HashFieldBase = six.with_metaclass(models.SubfieldBase, models.CharField)
else:
    HashFieldBase = models.CharField


class HashField(HashFieldBase):

    def __init__(self, *args, **kwargs):
        self.n_bytes = len(hashlib.sha1().hexdigest())
        kwargs['max_length'] = self.n_bytes

        super(HashField, self).__init__(*args, **kwargs)

    def construct(self, value):
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')
        return hashlib.sha1(value)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def db_type(self, connection=None):
        return 'char(%d)' % self.n_bytes
