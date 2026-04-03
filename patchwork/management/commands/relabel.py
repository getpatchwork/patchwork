# Patchwork - automated patch tracking system
# Copyright (C) 2026, The Linux Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.core.management.base import BaseCommand

from email.parser import HeaderParser

from patchwork.models import Label, Patch
from patchwork.parser import clean_subject


# Prepares a dictionary that maps from project id to a list of
# labels of this project (including global labels, if no local version exists)
def get_labels_per_project():
    global_labels = list(Label.objects.filter(project_id=None).all())

    labels_per_project = {}
    for label in Label.objects.filter(project_id__isnull=True).all():
        labels_list = labels_per_project.get(label.project_id, [])
        labels_list.append(label)
        labels_per_project[label.project_id] = labels_list

    for project_labels in labels_per_project.values():
        local_label_names = [label.name for label in project_labels]
        for global_label in global_labels:
            if global_label.name not in local_label_names:
                project_labels.append(global_label)

    return labels_per_project, global_labels


# Parses stripped name and labels out of patch headers
def get_name_and_labels(headers, labels):
    parser = HeaderParser()
    headers = parser.parsestr(headers)
    subject = headers['Subject']
    prefixes = []
    if subject is None:
        return None, None

    name, prefixes, cleaned_prefixes = clean_subject(subject, labels)

    return name, cleaned_prefixes


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

    def flush(self, patch_obj):
        if len(self.patches_to_update) > 0:
            patch_obj.objects.bulk_update(self.patches_to_update, ['name'])
            self.patches_to_update = []
            self.patches_to_update_ids = set()

        if len(self.series_to_update) > 0:
            Series.objects.bulk_update(self.series_to_update, ['name'])
            self.series_to_update = []

        if len(self.labels_to_add) > 0:
            patch_obj.labels.through.objects.bulk_create(self.labels_to_add)
            self.labels_to_add = []

    def reset(self):
        self.patches_to_update = []
        self.series_to_update = []
        self.patches_to_update_ids = set()
        self.labels_to_add = []

    def update_patches(self, projects):
        self.reset()

        query = Patch.objects.all().only('id', 'headers', 'project_id')

        if projects:
            query = query.filter(project__listid__in=projects)

        count = query.count()

        for i, patch in enumerate(query.iterator(chunk_size=1000)):
            project_labels = self.labels_per_project.get(
                patch.project_id, self.global_labels
            )

            name, cleaned_prefixes = get_name_and_labels(
                patch.headers, [label.name for label in project_labels]
            )
            if name is None or cleaned_prefixes is None:
                continue

            for label in project_labels:
                if (
                    label.name in cleaned_prefixes
                    and label not in patch.labels.all()
                ):
                    self.labels_to_add.append(
                        Patch.labels.through(
                            patch_id=patch.id, label_id=label.id
                        )
                    )
                    self.patches_to_update_ids.add(patch.id)

            if patch.name != name:
                patch.name = name[:255]
                self.patches_to_update.append(patch)

            if (
                patch.series is not None
                and patch.series.name != name
                and patch.number == 1
                and patch.series.cover_letter is None
            ):
                patch.series.name = name[:255]
                self.series_to_update.append(patch.series)

            if (i % 100) == 0:
                self.stdout.write('%06d/%06d\r' % (i, count), ending='')
                self.stdout.flush()

            if len(self.patches_to_update) >= 1000:
                self.flush(Patch)

        self.flush(Patch)

    def handle(self, *args, **options):
        self.labels_per_project, self.global_labels = get_labels_per_project()

        self.stdout.write('\nupdating patches')

        self.update_patches(options['projects'])

        self.stdout.write('\ndone')
