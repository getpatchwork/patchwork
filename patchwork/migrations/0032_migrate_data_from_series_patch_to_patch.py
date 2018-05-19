# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import Count
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0031_add_patch_series_fields'),
    ]

    operations = [
        # Copy SeriesPatch.series, SeriesPatch.number to Patch.series_alt,
        # Patch.number. Note that there is no uniqueness check here because no
        # code actually allowed us to save multiple series
        migrations.RunSQL(
            """UPDATE patchwork_patch SET series_alt_id =
                  (SELECT series_id from patchwork_seriespatch
                   WHERE patchwork_seriespatch.patch_id =
                            patchwork_patch.submission_ptr_id);
               UPDATE patchwork_patch SET number =
                   (SELECT number from patchwork_seriespatch
                    WHERE patchwork_seriespatch.patch_id =
                             patchwork_patch.submission_ptr_id);
            """,
            """INSERT INTO patchwork_seriespatch
                  (patch_id, series_id, number)
                SELECT submission_ptr_id, series_alt_id, number
                FROM patchwork_patch;
            """,
        ),
    ]
