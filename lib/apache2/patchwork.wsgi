#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Apache2 WSGI handler for patchwork
#
# Copyright © 2010 martin f. krafft <madduck@madduck.net>
# Released under the GNU General Public License v2 or later.
#
import os
import sys

basedir = os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)
sys.path.append(basedir)
sys.path.append(os.path.join(basedir, 'apps'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
