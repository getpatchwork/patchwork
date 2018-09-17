#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Patchwork - automated patch tracking system
# Copyright (C) 2010 Martin F. Krafft <madduck@madduck.net>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'patchwork.settings.production'

application = get_wsgi_application()
