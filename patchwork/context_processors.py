# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib.sites.models import Site

import patchwork


def site(request):
    return {'site': Site.objects.get_current()}


def version(request):
    return {'version': patchwork.__version__}
