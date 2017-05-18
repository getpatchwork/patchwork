# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patch',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patchwork.State', null=True),
        ),
    ]
