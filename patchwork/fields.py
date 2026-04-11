# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import hashlib

from django.db import models


class HashField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.n_bytes = len(hashlib.sha1(usedforsecurity=False).hexdigest())
        kwargs['max_length'] = self.n_bytes

        super(HashField, self).__init__(*args, **kwargs)

    def construct(self, value):
        # TODO: should this be unconditional?
        if isinstance(value, str):
            value = value.encode('utf-8')
        return hashlib.sha1(value, usedforsecurity=False)

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def db_type(self, connection=None):
        return 'char(%d)' % self.n_bytes


class ColorField(models.Field):
    description = 'Hex color code'

    def get_internal_type(self):
        return 'PositiveIntegerField'

    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        return '#%06x' % value

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def get_prep_value(self, value):
        return int(value.lstrip('#'), 16)

    def formfield(self, *args, **kwargs):
        from patchwork import forms  # noqa

        kwargs['form_class'] = forms.ColorField
        return super(ColorField, self).formfield(*args, **kwargs)
