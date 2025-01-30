from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0047_add_database_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='dependencies',
            field=models.ManyToManyField(
                blank=True,
                help_text='Optional dependencies on this patch.',
                related_name='dependents',
                related_query_name='dependent',
                to='patchwork.series',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='show_dependencies',
            field=models.BooleanField(
                default=False,
                help_text='Enable dependency tracking for patches and cover '
                'letters.',
            ),
        ),
        migrations.AlterField(
            model_name='series',
            name='cover_letter',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='series',
                to='patchwork.cover',
            ),
        ),
    ]
