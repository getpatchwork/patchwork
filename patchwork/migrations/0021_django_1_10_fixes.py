# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0020_tag_show_column'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='series',
            options={'ordering': ('date',), 'verbose_name_plural': 'Series'},
        ),
    ]

    if django.VERSION >= (1, 10):
        operations += [
            migrations.AlterModelOptions(
                name='patch',
                options={'base_manager_name': 'objects', 'verbose_name_plural': 'Patches'},
            ),
        ]
