# Patchwork - automated patch tracking system
# Copyright (C) 2020, Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.fields import empty
from rest_framework.fields import get_attribute
from rest_framework.fields import SkipField
from rest_framework.relations import ManyRelatedField


# monkey patch django-rest-framework to work around issue #7550 [1] until #7574
# [2] or some other variant lands
#
# [1] https://github.com/encode/django-rest-framework/issues/7550
# [2] https://github.com/encode/django-rest-framework/pull/7574

def _get_attribute(self, instance):
    # Can't have any relationships if not created
    if hasattr(instance, 'pk') and instance.pk is None:
        return []

    try:
        relationship = get_attribute(instance, self.source_attrs)
    except (KeyError, AttributeError) as exc:
        if self.default is not empty:
            return self.get_default()
        if self.allow_null:
            return None
        if not self.required:
            raise SkipField()
        msg = (
            'Got {exc_type} when attempting to get a value for field '
            '`{field}` on serializer `{serializer}`.\nThe serializer '
            'field might be named incorrectly and not match '
            'any attribute or key on the `{instance}` instance.\n'
            'Original exception text was: {exc}.'.format(
                exc_type=type(exc).__name__,
                field=self.field_name,
                serializer=self.parent.__class__.__name__,
                instance=instance.__class__.__name__,
                exc=exc
            )
        )
        raise type(exc)(msg)

    return relationship.all() if hasattr(relationship, 'all') else relationship


ManyRelatedField.get_attribute = _get_attribute
