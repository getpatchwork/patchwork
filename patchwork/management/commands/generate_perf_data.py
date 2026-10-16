# Patchwork - automated patch tracking system
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import random
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import reset_queries
from django.db import transaction

from patchwork.hasher import hash_diff
from patchwork.models import Patch
from patchwork.models import PatchComment
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import State


DIFF = '''diff --git a/example.txt b/example.txt
--- a/example.txt
+++ b/example.txt
@@ -1 +1 @@
-before
+after
'''


class Command(BaseCommand):
    help = 'Generate synthetic projects and patches for performance testing'

    def add_arguments(self, parser):
        parser.add_argument('--projects', type=int, default=12)
        parser.add_argument('--patches-per-project', type=int, default=100000)
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--max-series-size', type=int, default=10)
        parser.add_argument('--open-series-percent', type=int, default=20)
        parser.add_argument('--archived-percent', type=int, default=10)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--prefix', default='perf')

    def handle(self, *args, **options):
        for option in (
            'projects',
            'patches_per_project',
            'batch_size',
            'max_series_size',
        ):
            if options[option] < 1:
                raise CommandError(f'{option.replace("_", "-")} must be > 0')
        if options['max_series_size'] > 32767:
            raise CommandError('max-series-size must be <= 32767')
        for option in ('open_series_percent', 'archived_percent'):
            if not 0 <= options[option] <= 100:
                raise CommandError(
                    f'{option.replace("_", "-")} must be between 0 and 100'
                )
        prefix = options['prefix']
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', prefix):
            raise CommandError('prefix must be a slug of 1 to 64 characters')

        names = [f'{prefix}-{i + 1}' for i in range(options['projects'])]
        emails = [f'{prefix}-{i + 1}@example.invalid' for i in range(100)]
        if Project.objects.filter(linkname__in=names).exists() or (
            Project.objects.filter(name__in=names).exists()
        ):
            raise CommandError(
                'Generated projects already exist; use a new prefix'
            )
        if Person.objects.filter(email__in=emails).exists():
            raise CommandError(
                'Generated people already exist; use a new prefix'
            )
        open_state = State.objects.filter(action_required=True).first()
        closed_state = State.objects.filter(action_required=False).first()
        if not open_state or not closed_state:
            raise CommandError(
                'An actionable and a non-actionable state are required. '
                'Load default_states first.'
            )

        rng = random.Random(options['seed'])  # noqa: S311
        Person.objects.bulk_create(
            [
                Person(email=email, name=f'Test submitter {i + 1}')
                for i, email in enumerate(emails)
            ]
        )
        # Query IDs explicitly: not every backend returns them on bulk insert.
        people = list(
            Person.objects.filter(email__in=emails).order_by('email')
        )
        total_series = 0
        total_replies = 0
        for name in names:
            project = Project.objects.create(
                linkname=name,
                name=name,
                listid=f'{name}.example.invalid',
                listemail=f'{name}@example.invalid',
                use_tags=False,
            )
            count, replies = self.generate_project(
                project, people, open_state, closed_state, rng, options
            )
            total_series += count
            total_replies += replies
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {len(names)} projects, {total_series} series, '
                f'{len(names) * options["patches_per_project"]} patches and '
                f'{total_replies} replies.'
            )
        )

    def generate_project(
        self, project, people, open_state, closed_state, rng, options
    ):
        remaining = options['patches_per_project']
        series_count = 0
        patch_count = 0
        reply_count = 0
        diff_hash = hash_diff(DIFF)
        # A fixed anchor makes dates reproducible as well as relationships.
        anchor = datetime.datetime(2025, 1, 1)
        if settings.USE_TZ:
            anchor = anchor.replace(tzinfo=datetime.timezone.utc)
        while remaining:
            series_batch = []
            patches = []
            while remaining and len(patches) < options['batch_size']:
                size = min(
                    rng.randint(1, options['max_series_size']),
                    remaining,
                    options['batch_size'] - len(patches),
                )
                series_count += 1
                date = anchor - datetime.timedelta(
                    seconds=rng.randrange(365 * 24 * 60 * 60)
                )
                series = Series(
                    project=project,
                    name=f'Synthetic series {series_count}',
                    date=date,
                    submitter=rng.choice(people),
                    total=size,
                )
                series_batch.append(series)
                is_open = rng.randrange(100) < options['open_series_percent']
                # Guarantee one match for open series, at a varied position.
                actionable = rng.randint(1, size) if is_open else None
                for number in range(1, size + 1):
                    archived = rng.randrange(100) < options['archived_percent']
                    state = rng.choice((open_state, closed_state))
                    if number == actionable:
                        archived, state = False, open_state
                    elif not is_open and not archived:
                        state = closed_state
                    patch_count += 1
                    patches.append(
                        Patch(
                            project=project,
                            series=series,
                            number=number,
                            name=f'[PATCH {number}/{size}] {series.name}',
                            msgid=f'<{project.linkname}-{patch_count}@example.invalid>',
                            date=date,
                            submitter=series.submitter,
                            state=state,
                            archived=archived,
                            content='Synthetic performance test patch.\n',
                            diff=DIFF,
                            hash=diff_hash,
                        )
                    )
                remaining -= size

            # Bulk inserts intentionally bypass save hooks, tags and events.
            with transaction.atomic():
                Series.objects.bulk_create(series_batch)
                saved_series = {
                    series.name: series
                    for series in Series.objects.filter(
                        project=project,
                        name__in=[series.name for series in series_batch],
                    )
                }
                for patch in patches:
                    patch.series = saved_series[patch.series.name]
                Patch.objects.bulk_create(patches)
                # As with series, query IDs for backends that don't return
                # primary keys after bulk inserts.
                patch_ids = dict(
                    Patch.objects.filter(
                        project=project,
                        msgid__in=[patch.msgid for patch in patches],
                    ).values_list('msgid', 'pk')
                )
                replies = []
                for patch in patches:
                    date = patch.date
                    for number in range(1, rng.randint(1, 10) + 1):
                        date += datetime.timedelta(
                            minutes=rng.randint(1, 24 * 60)
                        )
                        replies.append(
                            PatchComment(
                                patch_id=patch_ids[patch.msgid],
                                msgid=f'<reply-{number}-{patch.msgid[1:]}',
                                date=date,
                                submitter=rng.choice(people),
                                headers=(
                                    f'In-Reply-To: {patch.msgid}\n'
                                    f'References: {patch.msgid}\n'
                                ),
                                content='Synthetic performance test reply.\n',
                            )
                        )
                        reply_count += 1
                        if len(replies) >= options['batch_size']:
                            PatchComment.objects.bulk_create(replies)
                            replies = []
                if replies:
                    PatchComment.objects.bulk_create(replies)
            # Development settings enable DEBUG; don't retain millions of SQL
            # queries in memory while generating a large dataset.
            reset_queries()
            if options['verbosity']:
                self.stdout.write(
                    f'{project.linkname}: {patch_count}/'
                    f'{options["patches_per_project"]} patches'
                )
        return series_count, reply_count
