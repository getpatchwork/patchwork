from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0014_remove_userprofile_primary_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeriesReference',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('msgid', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'name',
                    models.CharField(
                        blank=True,
                        help_text=b'An optional name to associate with the '
                                  b'series, e.g. "John\'s PCI series".',
                        max_length=255,
                        null=True,
                    ),
                ),
                ('date', models.DateTimeField()),
                (
                    'version',
                    models.IntegerField(
                        default=1,
                        help_text=b'Version of series as indicated by the '
                                  b'subject prefix(es)',
                    ),
                ),
                (
                    'total',
                    models.IntegerField(
                        help_text=b'Number of patches in series as indicated '
                                  b'by the subject prefix(es)'
                    ),
                ),
                (
                    'cover_letter',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='series',
                        to='patchwork.CoverLetter',
                    ),
                ),
            ],
            options={'ordering': ('date',)},
        ),
        migrations.CreateModel(
            name='SeriesPatch',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'number',
                    models.PositiveSmallIntegerField(
                        help_text=b'The number assigned to this patch in the '
                                  b'series'
                    ),
                ),
                (
                    'patch',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Patch',
                    ),
                ),
                (
                    'series',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Series',
                    ),
                ),
            ],
            options={'ordering': ['number']},
        ),
        migrations.AddField(
            model_name='series',
            name='patches',
            field=models.ManyToManyField(
                related_name='series',
                through='patchwork.SeriesPatch',
                to='patchwork.Patch',
            ),
        ),
        migrations.AddField(
            model_name='series',
            name='submitter',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Person',
            ),
        ),
        migrations.AddField(
            model_name='seriesreference',
            name='series',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='references',
                related_query_name=b'reference',
                to='patchwork.Series',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='seriespatch',
            unique_together=set([('series', 'patch'), ('series', 'number')]),
        ),
    ]
