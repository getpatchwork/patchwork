# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0005_unselectable_maintainer_projects'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patch',
            old_name='content',
            new_name='diff',
        ),
        migrations.AddField(
            model_name='patch',
            name='content',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='patch',
            field=models.ForeignKey(related_query_name=b'comment',
                                    related_name='comments',
                                    to='patchwork.Patch'),
        ),
    ]
