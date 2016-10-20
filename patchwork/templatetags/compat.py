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

"""Compatibility wrappers for various Django versions."""

import django
from django.template import defaulttags
from django.template import Library


register = Library()


# cycle
#
# The cycle template tag enables auto-escaping by default in 1.8, with
# deprecations enabled in 1.7. A 'future' library is provided in 1.6
# to mitigate this, but it is removed in 1.10. Provide our own version
# of 'future' to ensure this works in all versions of Django supported.
#
# https://docs.djangoproject.com/en/dev/releases/1.6/
# https://docs.djangoproject.com/en/dev/releases/1.10/

@register.tag
def cycle(parser, token):
    if django.VERSION < (1, 8):
        return defaulttags.cycle(parser, token, escape=True)
    else:
        return defaulttags.cycle(parser, token)
