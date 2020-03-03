# Patchwork - automated patch tracking system
# Copyright (C) 2019, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime
import tarfile
import tempfile

from django.core.management import BaseCommand
from django.core.management import CommandError
from django.utils.encoding import force_bytes

from patchwork.models import Patch
from patchwork.models import Project
from patchwork.views.utils import patch_to_mbox


class Command(BaseCommand):
    help = 'Export patchwork projects as tarball of mbox files'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--compress', action='store_true',
            help='compress generated archive.',
        )
        parser.add_argument(
            'projects', metavar='PROJECT', nargs='*',
            help='list ID of project(s) to export. If not supplied, all '
            'projects will be exported.',
        )

    def handle(self, *args, **options):
        if options['projects']:
            projects = []
            for listid in options['projects']:
                try:
                    projects.append(Project.objects.get(listid=listid))
                except Project.DoesNotExist:
                    raise CommandError('Project not found: %s' % listid)
        else:
            projects = list(Project.objects.all())

        name = 'patchwork_dump_' + datetime.now().strftime('%Y_%m_%d_%H%M%S')

        if options['compress']:
            name += '.tar.gz'
            compress_level = 9
        else:
            name += '.tar'
            compress_level = 1

        self.stdout.write('Generating patch archive...')

        with tarfile.open(name, 'w:gz', compresslevel=compress_level) as tar:
            for i, project in enumerate(projects):
                self.stdout.write('Project %02d/%02d (%s)' % (
                    i + 1, len(projects), project.linkname))

                with tempfile.NamedTemporaryFile(delete=False) as mbox:
                    patches = Patch.objects.filter(project=project)
                    count = patches.count()
                    for j, patch in enumerate(patches):
                        if not (j % 10):
                            self.stdout.write('%06d/%06d\r' % (j, count),
                                              ending='')
                            self.stdout.flush()

                        mbox.write(force_bytes(patch_to_mbox(patch) + '\n'))

                tar.add(mbox.name, arcname='%s.mbox' % project.linkname)

        self.stdout.write('Dumped patch archive to %r' % name)
