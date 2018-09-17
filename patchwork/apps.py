# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.apps import AppConfig


class PatchworkAppConfig(AppConfig):

    name = 'patchwork'
    verbose_name = 'Patchwork'

    def ready(self):
        import patchwork.signals  # noqa
