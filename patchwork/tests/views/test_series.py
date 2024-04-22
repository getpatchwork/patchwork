# Patchwork - automated patch tracking system
# Copyright (C) 2024 Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt

from django.test import TestCase
from django.urls import reverse

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

    def test_series_list(self):
        requested_url = reverse(
            'series-list',
            kwargs={'project_id': self.project.linkname},
        )
        response = self.client.get(requested_url)

        self.assertEqual(response.status_code, 200)
