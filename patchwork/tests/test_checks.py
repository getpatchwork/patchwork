# Patchwork - automated patch tracking system
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt
from datetime import timedelta

from django.test import TransactionTestCase

from patchwork.models import Check
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_user


class PatchChecksTest(TransactionTestCase):

    def setUp(self):
        self.patch = create_patches()[0]
        self.user = create_user()

    def _create_check(self, **kwargs):
        values = {
            'patch': self.patch,
            'user': self.user,
        }
        values.update(**kwargs)

        return create_check(**values)

    def assertCheckEqual(self, patch, check_state):  # noqa
        state_names = dict(Check.STATE_CHOICES)
        self.assertEqual(self.patch.combined_check_state,
                         state_names[check_state])

    def assertChecksEqual(self, patch, checks=None):  # noqa
        if not checks:
            checks = []

        self.assertEqual(len(self.patch.checks), len(checks))
        self.assertEqual(
            sorted(self.patch.checks, key=lambda check: check.id),
            sorted(checks, key=lambda check: check.id))

    def assertCheckCountEqual(self, patch, total, state_counts=None):  # noqa
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

    def test_checks__no_checks(self):
        self.assertChecksEqual(self.patch, [])

    def test_checks__single_check(self):
        check = self._create_check()
        self.assertChecksEqual(self.patch, [check])

    def test_checks__multiple_checks(self):
        check_a = self._create_check()
        check_b = self._create_check(context='new-context/test1')
        self.assertChecksEqual(self.patch, [check_a, check_b])

    def test_checks__duplicate_checks(self):
        self._create_check(date=(dt.utcnow() - timedelta(days=1)))
        check = self._create_check()
        # this isn't a realistic scenario (dates shouldn't be set by user so
        # they will always increment), but it's useful to verify the removal
        # of older duplicates by the function
        self._create_check(date=(dt.utcnow() - timedelta(days=2)))
        self.assertChecksEqual(self.patch, [check])

    def test_checks__nultiple_users(self):
        check_a = self._create_check()
        check_b = self._create_check(user=create_user())
        self.assertChecksEqual(self.patch, [check_a, check_b])

    def test_check_count__no_checks(self):
        self.assertCheckCountEqual(self.patch, 0)

    def test_check_count__single_check(self):
        self._create_check()
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

    def test_check_count__multiple_checks(self):
        self._create_check(date=(dt.utcnow() - timedelta(days=1)))
        self._create_check(context='new/test1')
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_SUCCESS: 2})

    def test_check_count__multiple_users(self):
        self._create_check()
        self._create_check(user=create_user())
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_SUCCESS: 2})

    def test_check_count__duplicate_check_same_state(self):
        self._create_check(date=(dt.utcnow() - timedelta(days=1)))
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

        self._create_check()
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_SUCCESS: 1})

    def test_check_count__duplicate_check_new_state(self):
        self._create_check(date=(dt.utcnow() - timedelta(days=1)))
        self.assertCheckCountEqual(self.patch, 1, {Check.STATE_SUCCESS: 1})

        self._create_check(state=Check.STATE_FAIL)
        self.assertCheckCountEqual(self.patch, 2, {Check.STATE_FAIL: 1})

    def test_check__no_checks(self):
        self.assertCheckEqual(self.patch, Check.STATE_PENDING)

    def test_check__single_check(self):
        self._create_check()
        self.assertCheckEqual(self.patch, Check.STATE_SUCCESS)

    def test_check__failure_check(self):
        self._create_check()
        self._create_check(context='new/test1', state=Check.STATE_FAIL)
        self.assertCheckEqual(self.patch, Check.STATE_FAIL)

    def test_check__warning_check(self):
        self._create_check()
        self._create_check(context='new/test1', state=Check.STATE_WARNING)
        self.assertCheckEqual(self.patch, Check.STATE_WARNING)

    def test_check__success_check(self):
        self._create_check()
        self._create_check(context='new/test1')
        self.assertCheckEqual(self.patch, Check.STATE_SUCCESS)
