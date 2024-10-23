# Patchwork - automated patch tracking system
# Copyright (C) 2015 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.core.management.base import BaseCommand
from patchwork.models import Patch
from patchwork.api.patch import PatchReviewIntentionSerializer


class Command(BaseCommand):
    help = 'Updates the patch has_planned_review field'

    def handle(self, *args, **kwargs):
        for patch in Patch.objects.all():
            has_planned_review = False
            for (
                patch_interest
            ) in patch.planning_to_review.through.objects.filter(patch=patch):
                serializer = PatchReviewIntentionSerializer(patch_interest)
                if not serializer.data['is_stale']:
                    has_planned_review = True
                    break
            patch.has_planned_review = has_planned_review
            patch.save()
