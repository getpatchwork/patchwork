from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0032_migrate_data_from_series_patch_to_patch'),
    ]

    operations = [
        # Remove SeriesPatch
        migrations.AlterUniqueTogether(
            name='seriespatch', unique_together=set([]),
        ),
        migrations.RemoveField(model_name='seriespatch', name='patch',),
        migrations.RemoveField(model_name='seriespatch', name='series',),
        migrations.RemoveField(model_name='series', name='patches',),
        migrations.DeleteModel(name='SeriesPatch',),
        # Now that SeriesPatch has been removed, we can use the now-unused
        # Patch.series field and add a backreference
        migrations.RenameField(
            model_name='patch', old_name='series_alt', new_name='series',
        ),
        migrations.AlterField(
            model_name='patch',
            name='series',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='patches',
                related_query_name='patch',
                to='patchwork.Series',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='patch', unique_together=set([('series', 'number')]),
        ),
        # Migrate CoverLetter to OneToOneField as a cover letter can no longer
        # be assigned to multiple series
        migrations.AlterField(
            model_name='series',
            name='cover_letter',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='series',
                to='patchwork.CoverLetter',
            ),
        ),
    ]
