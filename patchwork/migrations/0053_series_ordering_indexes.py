# SPDX-License-Identifier: GPL-2.0-or-later

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0052_patch_filter_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='series',
            index=models.Index(
                fields=['project', 'date', 'id'],
                name='series_project_date_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='series',
            index=models.Index(
                fields=['project', 'name', 'id'],
                name='series_project_name_idx',
            ),
        ),
    ]
