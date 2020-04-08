from django.db import migrations, models
import django.db.models.deletion


def forward(apps, schema_editor):
    """Populate the project field from child cover letter/patches."""
    # TODO(stephenfin): Perhaps we'd like to include an SQL variant of the
    # below though I'd imagine it would be rather tricky
    Series = apps.get_model('patchwork', 'Series')

    for series in Series.objects.all():
        if series.cover_letter:
            series.project = series.cover_letter.project
            series.save()
        elif series.patches:
            patch = series.patches.first()
            if patch:
                series.project = patch.project
                series.save()
        else:
            # a series without patches or cover letters should not exist.
            # Delete it.
            series.delete()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    # This is necessary due to a mistake made when writing the migration.
    # PostgreSQL does not allow mixing of schema and data migrations within the
    # same transaction. Disabling transactions ensures this doesn't happen.
    # Refer to bug #104 for more information.
    atomic = False

    dependencies = [
        ('patchwork', '0015_add_series_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='series',
                to='patchwork.Project',
            ),
        ),
        migrations.RunPython(forward, reverse, atomic=False),
        migrations.AlterField(
            model_name='seriesreference',
            name='msgid',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='seriesreference', unique_together=set([('series', 'msgid')]),
        ),
    ]
