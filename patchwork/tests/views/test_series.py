# Patchwork - automated patch tracking system
# Copyright (C) 2012 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt

from django.test import TestCase
from django.urls import reverse

from patchwork.models import Patch
from patchwork.models import Person
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user


class SeriesList(TestCase):
    def setUp(self):
        self.project = create_project()
        self.user = create_user()
        self.person_1 = Person.objects.get(user=self.user)
        self.person_2 = create_person()
        self.series_1 = create_series(project=self.project)
        self.series_2 = create_series(project=self.project)
        create_cover(project=self.project, series=self.series_1)

        for i in range(5):
            create_patch(
                submitter=self.person_1,
                project=self.project,
                series=self.series_1,
                date=dt(2014, 3, 16, 13, 4, 50, 155643),
            )
            create_patch(
                submitter=self.person_2,
                project=self.project,
                series=self.series_2,
                date=dt(2014, 3, 16, 13, 4, 50, 155643),
            )

        # with open('output.html', "w", encoding="utf-8") as file:
        #     file.write(response.content.decode('utf-8'))

    def test_series_list(self):
        requested_url = reverse(
            'series-list',
            kwargs={'project_id': self.project.linkname},
        )
        response = self.client.get(requested_url)

        self.assertEqual(response.status_code, 200)

    def test_update_series_list_unauth(self):
        requested_url = reverse(
            'series-list',
            kwargs={'project_id': self.project.linkname},
        )

        data = {'save': self.series_1.id, 'archived': 'True', 'state': '*'}
        response = self.client.post(requested_url, data)

        self.assertContains(
            response, 'You don&#x27;t have permissions to edit patch'
        )

    def test_update_series_list(self):
        requested_url = reverse(
            'series-list',
            kwargs={'project_id': self.project.linkname},
        )

        data = {'save': self.series_1.id, 'archived': 'True', 'state': '*'}
        self.client.login(
            username=self.user.username, password=self.user.username
        )
        _ = self.client.post(requested_url, data)

        patches = Patch.objects.filter(series=self.series_1)
        for patch in patches:
            self.assertEqual(patch.archived, True)
