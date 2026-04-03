# Patchwork - automated patch tracking system
# Copyright (C) 2026, The Linux Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.core.management.base import BaseCommand

from email.parser import HeaderParser

from patchwork.models import Label, Patch
from patchwork.parser import clean_subject


class Command(BaseCommand):
    help = (
        'Update labels for existing patches based on the subject line. '
        'NOTE: Labels have to be created in the admin interface first.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'projects',
            metavar='PROJECT',
            nargs='*',
            help='list of listIDs of projects to be relabeld',
        )

    def handle(self, *args, **options):
        query = Patch.objects.all().only('id', 'headers', 'project_id')
        labels_to_add = []

        labels_per_project = {}
        for label in Label.objects.all():
            tmp = labels_per_project.get(label.project_id, [])
            tmp.append(label.name)
            labels_per_project[label.project_id] = tmp

        patches_to_update = []
        patches_to_update_ids = set()

        if options['projects']:
            query = query.filter(project__listid__in=options['projects'])

        count = query.count()

        for i, patch in enumerate(query.iterator(chunk_size=1000)):
            parser = HeaderParser()
            headers = parser.parsestr(patch.headers)
            subject = headers['Subject']
            prefixes = []
            if subject is None:
                continue

            project_labels = labels_per_project.get(
                patch.project.id, []
            ) + labels_per_project.get(None, [])

            name, prefixes, cleaned_prefixes = clean_subject(
                subject, project_labels
            )

            for label in project_labels:
                if label in cleaned_prefixes and label not in patch.labels:
                    labels_to_add.append(
                        Patch.labels.through(
                            patch_id=patch.id, label_id=label.id
                        )
                    )
                    patch.labels.append(label)
                    if patch.id not in patches_to_update_ids:
                        patch.name = name[:255]
                        patches_to_update.append(patch)
                        patches_to_update_ids.add(patch.id)

            if (i % 100) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()

            if len(patches_to_update) >= 1000:
                Patch.objects.bulk_update(patches_to_update, ['name'])
                patches_to_update = []
                patches_to_update_ids = set()
            if len(labels_to_add) >= 1000:
                Patch.labels.through.objects.bulk_create(labels_to_add)
                labels_to_add = []

        if len(patches_to_update) > 0:
            Patch.objects.bulk_update(patches_to_update, ['name'])
            patches_to_update = []
            patches_to_update_ids = set()
        if len(labels_to_add) > 0:
            Patch.labels.through.objects.bulk_create(labels_to_add)
            labels_to_add = []

        self.stdout.write('\ndone')
