# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import sys
from io import StringIO

from django.core.management import call_command
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
        call_command('parsemail', infile=path)

        count = models.Patch.objects.all().count()
        self.assertEqual(count, 0)

    def test_missing_project_stdin(self):
        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        call_command('parsemail', infile=None)

        sys.stdin.close()
        count = models.Patch.objects.all().count()
        self.assertEqual(count, 0)

    def test_valid_path(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        call_command('parsemail', infile=path, list_id=project.listid)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_valid_stdin(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        call_command('parsemail', infile=None, list_id=project.listid)

        sys.stdin.close()

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_utf8_path(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0013-with-utf8-body.mbox')
        call_command('parsemail', infile=path, list_id=project.listid)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_utf8_stdin(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0013-with-utf8-body.mbox')
        sys.stdin.close()
        sys.stdin = open(path)
        call_command('parsemail', infile=None, list_id=project.listid)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

    def test_dup_mail(self):
        project = utils.create_project()
        utils.create_state()

        path = os.path.join(TEST_MAIL_DIR, '0001-git-pull-request.mbox')
        call_command('parsemail', infile=path, list_id=project.listid)

        count = models.Patch.objects.filter(project=project.id).count()
        self.assertEqual(count, 1)

        # the parser should return None, not throwing an exception
        # as this is a pretty normal part of life on a busy site
        call_command('parsemail', infile=path, list_id=project.listid)

        # this would be lovely but doesn't work because we caused an error in
        # the transaction and we have no way to reset it
        # count = models.Patch.objects.filter(project=project.id).count()
        # self.assertEqual(count, 1)


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
