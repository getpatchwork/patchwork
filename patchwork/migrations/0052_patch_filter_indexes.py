# SPDX-License-Identifier: GPL-2.0-or-later

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0051_patch_api_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='patch',
            index=models.Index(
                fields=['project', 'submitter', 'id'],
                name='patch_project_submitter_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='patch',
            index=models.Index(
                fields=['project', 'name', 'id'],
                name='patch_project_name_idx',
            ),
        ),
    ]
