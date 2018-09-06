# Patchwork - automated patch tracking system
# Copyright (C) 2015 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase

from patchwork.models import Event
from patchwork.tests import utils

BASE_FIELDS = ['previous_state', 'current_state', 'previous_delegate',
               'current_delegate']


def _get_events(**filters):
    # These are sorted by reverse normally, so reverse it once again
    return Event.objects.filter(**filters).order_by('date')


class _BaseTestCase(TestCase):

    def assertEventFields(self, event, parent_type='patch', **fields):
        for field_name in [x for x in BASE_FIELDS]:
            field = getattr(event, field_name)
            if field_name in fields:
                self.assertEqual(field, fields[field_name])
            else:
                self.assertIsNone(field)


class PatchCreateTest(_BaseTestCase):

    def test_patch_created(self):
        """No series, so patch dependencies implicitly exist."""
        patch = utils.create_patch()

        # This should raise the CATEGORY_PATCH_CREATED event only as there is
        # no series
        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_PATCH_CREATED)
        self.assertEqual(events[0].project, patch.project)
        self.assertEventFields(events[0])

    def test_patch_dependencies_present_series(self):
        """Patch dependencies already exist."""
        series = utils.create_series()
        patch = utils.create_patch(series=series)

        # This should raise both the CATEGORY_PATCH_CREATED and
        # CATEGORY_PATCH_COMPLETED events
        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)
        self.assertEqual(events[0].category, Event.CATEGORY_PATCH_CREATED)
        self.assertEqual(events[0].project, patch.project)
        self.assertEqual(events[1].category, Event.CATEGORY_PATCH_COMPLETED)
        self.assertEqual(events[1].project, patch.project)
        self.assertEventFields(events[0])
        self.assertEventFields(events[1])

        # This shouldn't be affected by another update to the patch
        patch.commit_ref = 'aac76f0b0f8dd657ff07bb32df369705696d4831'
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)

    def test_patch_dependencies_out_of_order(self):
        series = utils.create_series()
        patch_3 = utils.create_patch(series=series, number=3)
        patch_2 = utils.create_patch(series=series, number=2)

        # This should only raise the CATEGORY_PATCH_CREATED event for
        # both patches as they are both missing dependencies
        for patch in [patch_2, patch_3]:
            events = _get_events(patch=patch)
            self.assertEqual(events.count(), 1)
            self.assertEqual(events[0].category, Event.CATEGORY_PATCH_CREATED)
            self.assertEventFields(events[0])

        patch_1 = utils.create_patch(series=series, number=1)

        # We should now see the CATEGORY_PATCH_COMPLETED event for all patches
        # as the dependencies for all have been met
        for patch in [patch_1, patch_2, patch_3]:
            events = _get_events(patch=patch)
            self.assertEqual(events.count(), 2)
            self.assertEqual(events[0].category, Event.CATEGORY_PATCH_CREATED)
            self.assertEqual(events[1].category,
                             Event.CATEGORY_PATCH_COMPLETED)
            self.assertEventFields(events[0])
            self.assertEventFields(events[1])

    def test_patch_dependencies_missing(self):
        series = utils.create_series()
        patch = utils.create_patch(series=series, number=2)

        # This should only raise the CATEGORY_PATCH_CREATED event as
        # there is a missing dependency (patch 1)
        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_PATCH_CREATED)
        self.assertEventFields(events[0])


class PatchChangedTest(_BaseTestCase):

    def test_patch_state_changed(self):
        patch = utils.create_patch()
        old_state = patch.state
        new_state = utils.create_state()

        patch.state = new_state
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)
        # we don't care about the CATEGORY_PATCH_CREATED event here
        self.assertEqual(events[1].category,
                         Event.CATEGORY_PATCH_STATE_CHANGED)
        self.assertEqual(events[1].project, patch.project)
        self.assertEventFields(events[1], previous_state=old_state,
                               current_state=new_state)

    def test_patch_delegated(self):
        patch = utils.create_patch()
        delegate_a = utils.create_user()

        # None -> Delegate A

        patch.delegate = delegate_a
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)
        # we don't care about the CATEGORY_PATCH_CREATED event here
        self.assertEqual(events[1].category,
                         Event.CATEGORY_PATCH_DELEGATED)
        self.assertEqual(events[1].project, patch.project)
        self.assertEventFields(events[1], current_delegate=delegate_a)

        delegate_b = utils.create_user()

        # Delegate A -> Delegate B

        patch.delegate = delegate_b
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 3)
        self.assertEqual(events[2].category,
                         Event.CATEGORY_PATCH_DELEGATED)
        self.assertEventFields(events[2], previous_delegate=delegate_a,
                               current_delegate=delegate_b)

        # Delegate B -> None

        patch.delegate = None
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 4)
        self.assertEqual(events[3].category,
                         Event.CATEGORY_PATCH_DELEGATED)
        self.assertEventFields(events[3], previous_delegate=delegate_b)


class CheckCreateTest(_BaseTestCase):

    def test_check_created(self):
        check = utils.create_check()
        events = _get_events(created_check=check)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_CHECK_CREATED)
        self.assertEqual(events[0].project, check.patch.project)
        self.assertEventFields(events[0])


class CoverCreateTest(_BaseTestCase):

    def test_cover_created(self):
        cover = utils.create_cover()
        events = _get_events(cover=cover)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_COVER_CREATED)
        self.assertEqual(events[0].project, cover.project)
        self.assertEventFields(events[0])


class SeriesCreateTest(_BaseTestCase):

    def test_series_created(self):
        series = utils.create_series()
        events = _get_events(series=series)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_SERIES_CREATED)
        self.assertEqual(events[0].project, series.project)
        self.assertEventFields(events[0])
