# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('patchwork', '0036_project_commit_url_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='actor',
            field=models.ForeignKey(
                blank=True,
                help_text=b'The user that caused/created this event.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
