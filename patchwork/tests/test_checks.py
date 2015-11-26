# Patchwork - automated patch tracking system
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

from datetime import datetime as dt
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.test import TransactionTestCase

from patchwork.models import Patch, Check
from patchwork.tests.utils import defaults, create_user


class PatchChecksTest(TransactionTestCase):
    fixtures = ['default_tags', 'default_states']

    def setUp(self):
        project = defaults.project
        defaults.project.save()
        defaults.patch_author_person.save()
        self.patch = Patch(project=project,
                           msgid='x', name=defaults.patch_name,
                           submitter=defaults.patch_author_person,
                           content='')
        self.patch.save()
        self.user = create_user()

    def create_check(self, **kwargs):
        check_values = {
            'patch': self.patch,
            'user': self.user,
            'date': dt.now(),
            'state': Check.STATE_SUCCESS,
            'target_url': 'http://example.com/',
            'description': '',
            'context': 'intel/jenkins-ci',
        }

        for key in check_values:
            if key in kwargs:
                check_values[key] = kwargs[key]

        check = Check(**check_values)
        check.save()
        return check

    def assertCheckEqual(self, patch, check_state):
        self.assertEqual(self.patch.combined_check_state, check_state)

    def assertChecksEqual(self, patch, checks=None):
        if not checks:
            checks = []

        self.assertEqual(len(self.patch.checks), len(checks))
        self.assertEqual(
            sorted(self.patch.checks, key=lambda check: check.id),
            sorted(checks, key=lambda check: check.id))

    def assertCheckCountEqual(self, patch, total, state_counts=None):
        if not state_counts:
            state_counts = {}

        counts = self.patch.check_count

        self.assertEqual(self.patch.check_set.count(), total)

        for state in state_counts:
            self.assertEqual(counts[state], state_counts[state])

        # also check the ones we didn't explicitly state
        for state, _ in Check.STATE_CHOICES:
            if state not in state_counts:
                self.assertEqual(counts[state], 0)

    def tearDown(self):
        self.patch.delete()

    def test_checks__no_checks(self):
        self.assertChecksEqual(self.patch, [])

    def test_checks__single_check(self):
        check = self.create_check()
        self.assertChecksEqual(self.patch, [check])

    def test_checks__multiple_checks(self):
        check_a = self.create_check()
        check_b = self.create_check(context='new-context/test1')
        self.assertChecksEqual(self.patch, [check_a, check_b])

    def test_checks__duplicate_checks(self):
        check_a = self.create_check(date=(dt.now() - timedelta(days=1)))
        check_b = self.create_check()
        # this isn't a realistic scenario (dates shouldn't be set by user so
        #   they will always increment), but it's useful to verify the removal
        #   of older duplicates by the function
        check_c = self.create_check(date=(dt.now() - timedelta(days=2)))
        self.assertChecksEqual(self.patch, [check_b])

    def test_check_count__no_checks(self):
        self.assertCheckCountEqual(self.patch, 0)

    def test_check_count__single_check(self):
        self.create_check()
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

    def test_check_count__multiple_checks(self):
        self.create_check(date=(dt.now() - timedelta(days=1)))
        self.create_check(context='new/test1')
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_SUCCESS: 2})

    def test_check_count__duplicate_check_same_state(self):
        self.create_check(date=(dt.now() - timedelta(days=1)))
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

        self.create_check()
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_SUCCESS: 1})

    def test_check_count__duplicate_check_new_state(self):
        self.create_check(date=(dt.now() - timedelta(days=1)))
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

        self.create_check(state=Check.STATE_FAIL)
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_FAIL: 1})

    def test_check__no_checks(self):
        self.assertCheckEqual(self.patch, Check.STATE_PENDING)

    def test_check__single_check(self):
        self.create_check()
        self.assertCheckEqual(self.patch, Check.STATE_SUCCESS)

    def test_check__failure_check(self):
        self.create_check()
        self.create_check(context='new/test1', state=Check.STATE_FAIL)
        self.assertCheckEqual(self.patch, Check.STATE_FAIL)

    def test_check__warning_check(self):
        self.create_check()
        self.create_check(context='new/test1', state=Check.STATE_WARNING)
        self.assertCheckEqual(self.patch, Check.STATE_WARNING)

    def test_check__success_check(self):
        self.create_check()
        self.create_check(context='new/test1')
        self.assertCheckEqual(self.patch, Check.STATE_SUCCESS)

