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

import os
import sys

from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from patchwork import models
from patchwork.tests import TEST_MAIL_DIR
from patchwork.tests import utils


class ParsemailTest(TestCase):

    def test_invalid_path(self):
        # this can raise IOError, CommandError, or FileNotFoundError,
        # depending of the versions of Python and Django used. Just
        # catch a generic exception
        with self.assertRaises(Exception):
            call_command('parsemail', infile='xyz123random')

    def test_missing_project_path(self):
        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=path)

        self.assertEqual(exc.exception.code, 1)

    def test_missing_project_stdin(self):
        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=None)

        self.assertEqual(exc.exception.code, 1)

    def test_valid_path(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=path, list_id=project.listid)

        self.assertEqual(exc.exception.code, 0)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_valid_stdin(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=None,
                         list_id=project.listid)

        self.assertEqual(exc.exception.code, 0)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_utf8_path(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0013-with-utf8-body.mbox')
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=path, list_id=project.listid)

        self.assertEqual(exc.exception.code, 0)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_utf8_stdin(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0013-with-utf8-body.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail', infile=None,
                         list_id=project.listid)

        self.assertEqual(exc.exception.code, 0)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)


class ParsearchiveTest(TestCase):
    def test_invalid_path(self):
        out = StringIO()
        with self.assertRaises(SystemExit) as exc:
            call_command('parsearchive', 'xyz123random', stdout=out)
        self.assertEqual(exc.exception.code, 1)

    def test_invalid_mbox(self):
        out = StringIO()
        # we haven't created a project yet, so this will fail
        call_command('parsearchive',
                     os.path.join(TEST_MAIL_DIR,
                                  '0001-git-pull-request.mbox'),
                     stdout=out)

        self.assertIn('Processed 1 messages -->', out.getvalue())
        self.assertIn('  1 dropped', out.getvalue())
