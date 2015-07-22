# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patch',
            name='state',
            field=models.ForeignKey(to='patchwork.State', null=True),
        ),
    ]
