# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

import django
from django.conf import settings
from django.urls import reverse

from patchwork.models import Event
from patchwork.tests.api import utils
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_state

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestEventAPI(utils.APITestCase):

    @staticmethod
    def api_url(version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        return reverse('api-event-list', kwargs=kwargs)

    def assertSerialized(self, event_obj, event_json):
        self.assertEqual(event_obj.id, event_json['id'])
        self.assertEqual(event_obj.category, event_json['category'])
        if event_obj.actor is None:
            self.assertIsNone(event_json['actor'])

        # nested fields

        self.assertEqual(event_obj.project.id,
                         event_json['project']['id'])
        if event_obj.actor is not None:
            self.assertEqual(event_obj.actor.id,
                             event_json['actor']['id'])

        # TODO(stephenfin): Check other fields

    def test_list_empty(self):
        """List events when none are present."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

    def _create_events(self):
        """Create sample events.

        This one's a bit weird. While we could generate event models ourselves,
        it seems wiser to test the event machinery as many times as possible.
        As a result, we actually create a load of *other* objects, which will
        raise signals and trigger the remainder.
        """
        # series-created
        series = create_series()
        # patch-created, patch-completed, series-completed
        patch = create_patch(series=series)
        # cover-created
        create_cover(series=series)
        # check-created
        create_check(patch=patch)
        # patch-delegated, patch-state-changed
        actor = create_maintainer(project=patch.project)
        user = create_maintainer(project=patch.project)
        state = create_state()
        patch.delegate = user
        patch.state = state
        self.assertTrue(patch.is_editable(actor))
        patch.save()

        return Event.objects.all()

    @utils.store_samples('event-list')
    def test_list(self):
        """List events."""
        events = self._create_events()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(8, len(resp.data), [x['category'] for x in resp.data])
        for event_rsp in resp.data:
            event_obj = events.get(category=event_rsp['category'])
            self.assertSerialized(event_obj, event_rsp)

    def test_list_filter_project(self):
        """Filter events by project."""
        events = self._create_events()
        project = events[0].project
        create_series()  # create series in a random project

        resp = self.client.get(self.api_url(), {'project': project.pk})
        # All but one event belongs to the same project
        self.assertEqual(8, len(resp.data))

        resp = self.client.get(self.api_url(), {'project': 'invalidproject'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_category(self):
        """Filter events by category."""
        events = self._create_events()

        resp = self.client.get(self.api_url(),
                               {'category': events[0].category})
        # There should only be one
        self.assertEqual(1, len(resp.data))

        resp = self.client.get(
            self.api_url(),
            {'category': 'foo-bar'},
            validate_request=False,
        )
        self.assertEqual(0, len(resp.data))

    def test_list_filter_patch(self):
        """Filter events by patch."""
        events = self._create_events()

        patch = events.get(category='patch-created').patch
        resp = self.client.get(self.api_url(), {'patch': patch.pk})
        # There should be five - patch-created, patch-completed, check-created,
        # patch-state-changed and patch-delegated
        self.assertEqual(5, len(resp.data))

        resp = self.client.get(self.api_url(), {'patch': 999999})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_cover(self):
        """Filter events by cover."""
        events = self._create_events()

        cover = events.get(category='cover-created').cover
        resp = self.client.get(self.api_url(), {'cover': cover.pk})
        # There should only be one - cover-created
        self.assertEqual(1, len(resp.data))

        resp = self.client.get(self.api_url(), {'cover': 999999})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_series(self):
        """Filter events by series."""
        events = self._create_events()

        series = events.get(category='series-created').series
        resp = self.client.get(self.api_url(), {'series': series.pk})
        # There should be three - series-created, patch-completed and
        # series-completed
        self.assertEqual(3, len(resp.data))

        resp = self.client.get(self.api_url(), {'series': 999999})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_actor(self):
        """Filter events by actor."""
        events = self._create_events()

        # The final two events (patch-delegated, patch-state-changed)
        # have an actor set
        actor = events[0].actor
        resp = self.client.get(self.api_url(), {'actor': actor.pk})
        self.assertEqual(2, len(resp.data))

        resp = self.client.get(self.api_url(), {'actor': 'foo-bar'})
        self.assertEqual(0, len(resp.data))

    def test_list_filter_actor_version_1_1(self):
        """Filter events by actor using API v1.1."""
        events = self._create_events()

        # we still see all the events since the actor field is ignored
        resp = self.client.get(self.api_url(version='1.1'),
                               {'actor': 'foo-bar'})
        self.assertEqual(len(events), len(resp.data))

    def test_list_bug_335(self):
        """Ensure we retrieve the embedded series project once."""
        for _ in range(3):
            self._create_events()

        # TODO(stephenfin): Remove when we drop support for Django < 3.2
        num_queries = 28 if django.VERSION < (3, 2) else 27

        with self.assertNumQueries(num_queries):
            self.client.get(self.api_url())

    def test_order_by_date_default(self):
        """Assert the default ordering is by date descending."""
        self._create_events()

        resp = self.client.get(self.api_url())
        events = Event.objects.order_by("-date").all()
        for api_event, event in zip(resp.data, events):
            self.assertEqual(api_event["id"], event.id)

    def test_order_by_date_ascending(self):
        """Assert the default ordering is by date descending."""
        self._create_events()

        resp = self.client.get(self.api_url(), {'order': 'date'})
        events = Event.objects.order_by("date").all()
        for api_event, event in zip(resp.data, events):
            self.assertEqual(api_event["id"], event.id)

    def test_create(self):
        """Ensure creates aren't allowed"""
        user = create_maintainer()
        user.is_superuser = True
        user.save()

        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), {'category': 'patch-created'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
