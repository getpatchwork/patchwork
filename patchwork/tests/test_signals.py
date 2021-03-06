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


class PatchCreatedTest(_BaseTestCase):

    def test_patch_created(self):
        """No series, so patch dependencies implicitly exist."""
        patch = utils.create_patch(series=None)

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
        # purposefully setting series to None to minimize additional events
        patch = utils.create_patch(series=None)
        old_state = patch.state
        new_state = utils.create_state()
        actor = utils.create_maintainer(project=patch.project)

        patch.state = new_state
        self.assertTrue(patch.is_editable(actor))
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)
        # we don't care about the CATEGORY_PATCH_CREATED event here
        self.assertEqual(events[1].category,
                         Event.CATEGORY_PATCH_STATE_CHANGED)
        self.assertEqual(events[1].project, patch.project)
        self.assertEqual(events[1].actor, actor)
        self.assertEventFields(events[1], previous_state=old_state,
                               current_state=new_state)

    def test_patch_delegated(self):
        # purposefully setting series to None to minimize additional events
        patch = utils.create_patch(series=None)
        delegate_a = utils.create_user()
        actor = utils.create_maintainer(project=patch.project)

        # None -> Delegate A

        patch.delegate = delegate_a
        self.assertTrue(patch.is_editable(actor))
        patch.save()

        events = _get_events(patch=patch)
        self.assertEqual(events.count(), 2)
        # we don't care about the CATEGORY_PATCH_CREATED event here
        self.assertEqual(events[1].category,
                         Event.CATEGORY_PATCH_DELEGATED)
        self.assertEqual(events[1].project, patch.project)
        self.assertEqual(events[1].actor, actor)
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

    def test_patch_relations_changed(self):
        # purposefully setting series to None to minimize additional events
        relation = utils.create_relation()
        patches = utils.create_patches(3, series=None)

        # mark the first two patches as related; the second patch should be the
        # one that the event is raised for

        patches[0].related = relation
        patches[0].save()
        patches[1].related = relation
        patches[1].save()

        events = _get_events(patch=patches[1])
        self.assertEqual(events.count(), 2)
        self.assertEqual(
            events[1].category, Event.CATEGORY_PATCH_RELATION_CHANGED)
        self.assertEqual(events[1].project, patches[1].project)
        self.assertIsNone(events[1].previous_relation)
        self.assertIsNone(events[1].current_relation)

        # add the third patch

        patches[2].related = relation
        patches[2].save()

        events = _get_events(patch=patches[2])
        self.assertEqual(events.count(), 2)
        self.assertEqual(
            events[1].category, Event.CATEGORY_PATCH_RELATION_CHANGED)
        self.assertEqual(events[1].project, patches[1].project)
        self.assertIsNone(events[1].previous_relation)
        self.assertIsNone(events[1].current_relation)

        # drop the third patch

        patches[2].related = None
        patches[2].save()

        events = _get_events(patch=patches[2])
        self.assertEqual(events.count(), 3)
        self.assertEqual(
            events[2].category, Event.CATEGORY_PATCH_RELATION_CHANGED)
        self.assertEqual(events[2].project, patches[1].project)
        self.assertIsNone(events[2].previous_relation)
        self.assertIsNone(events[2].current_relation)


class CheckCreatedTest(_BaseTestCase):

    def test_check_created(self):
        check = utils.create_check()
        events = _get_events(created_check=check)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_CHECK_CREATED)
        self.assertEqual(events[0].project, check.patch.project)
        self.assertEqual(events[0].actor, check.user)
        self.assertEventFields(events[0])


class CoverCreatedTest(_BaseTestCase):

    def test_cover_created(self):
        cover = utils.create_cover()
        events = _get_events(cover=cover)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_COVER_CREATED)
        self.assertEqual(events[0].project, cover.project)
        self.assertEventFields(events[0])


class SeriesCreatedTest(_BaseTestCase):

    def test_series_created(self):
        series = utils.create_series()
        events = _get_events(series=series)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].category, Event.CATEGORY_SERIES_CREATED)
        self.assertEqual(events[0].project, series.project)
        self.assertEventFields(events[0])


class SeriesChangedTest(_BaseTestCase):

    def test_series_completed(self):
        """Validate 'series-completed' events."""
        series = utils.create_series(total=2)

        # the series has no patches associated with it so it's not yet complete
        events = _get_events(series=series)
        self.assertNotIn(Event.CATEGORY_SERIES_COMPLETED,
                         [x.category for x in events])

        # create the second of two patches in the series; series is still not
        # complete
        utils.create_patch(series=series, number=2)
        events = _get_events(series=series)
        self.assertNotIn(Event.CATEGORY_SERIES_COMPLETED,
                         [x.category for x in events])

        # now create the first patch, which will "complete" the series
        utils.create_patch(series=series, number=1)
        events = _get_events(series=series)
        self.assertIn(Event.CATEGORY_SERIES_COMPLETED,
                      [x.category for x in events])
