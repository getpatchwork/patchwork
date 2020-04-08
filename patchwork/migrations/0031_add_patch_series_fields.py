from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0030_add_submission_covering_index'),
    ]

    operations = [
        # Add Patch.series_alt, Patch.number fields. This will store the fields
        # currently stored in SeriesPatch
        migrations.AddField(
            model_name='patch',
            name='number',
            field=models.PositiveSmallIntegerField(
                default=None,
                help_text=b'The number assigned to this patch in the series',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='series_alt',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Series',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='patch', unique_together=set([('series_alt', 'number')]),
        ),
    ]
