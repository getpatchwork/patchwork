# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def copy_series_field(apps, schema_editor):
    """Populate the project field from child cover letter/patches."""
    # TODO(stephenfin): Perhaps we'd like to include an SQL variant of the
    # below though I'd imagine it would be rather tricky
    Series = apps.get_model('patchwork', 'Series')

    for series in Series.objects.all():
        if series.cover_letter:
            series.project = series.cover_letter.project
            series.save()
        elif series.patches:
            series.project = series.patches.first().project
            series.save()
        else:
            # a series without patches or cover letters should not exist.
            # Delete it.
            series.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0015_add_series_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='series', to='patchwork.Project'),
        ),
        migrations.RunPython(copy_series_field, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='seriesreference',
            name='msgid',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='seriesreference',
            unique_together=set([('series', 'msgid')]),
        ),
    ]
