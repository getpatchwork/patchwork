# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import patchwork.models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0024_patch_patch_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='subject_match',
            field=models.CharField(blank=True, default=b'', help_text=b'Regex to match the subject against if only part of emails sent to the list belongs to this project. Will be used with IGNORECASE and MULTILINE flags. If rules for more projects match the first one returned from DB is chosen; empty field serves as a default for every email which has no other match.', max_length=64, validators=[patchwork.models.validate_regex_compiles]),
        ),
        migrations.AlterField(
            model_name='tag',
            name='pattern',
            field=models.CharField(help_text=b'A simple regex to match the tag in the content of a message. Will be used with MULTILINE and IGNORECASE flags. eg. ^Acked-by:', max_length=50, validators=[patchwork.models.validate_regex_compiles]),
        ),
    ]
