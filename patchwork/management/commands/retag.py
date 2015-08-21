
from django.core.management.base import BaseCommand, CommandError
from patchwork.models import Patch
import sys

class Command(BaseCommand):
    help = 'Update the tag (Ack/Review/Test) counts on existing patches'
    args = '[<patch_id>...]'

    def handle(self, *args, **options):

        qs = Patch.objects

        if args:
            qs = qs.filter(id__in=args)
        else:
            qs = qs.all()

        count = qs.count()
        i = 0

        for patch in qs.iterator():
            patch.refresh_tag_counts()
            i += 1
            if (i % 10) == 0 or i == count:
                sys.stdout.write('%06d/%06d\r' % (i, count))
                sys.stdout.flush()
        sys.stderr.write('\ndone\n')
