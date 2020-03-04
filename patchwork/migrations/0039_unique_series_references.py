from django.db import connection, migrations, models
from django.db.models import Count
import django.db.models.deletion


def copy_project_field(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute(
            """
            UPDATE patchwork_seriesreference
              SET project_id = patchwork_series.project_id
            FROM patchwork_series
              WHERE patchwork_seriesreference.series_id = patchwork_series.id
            """
        )
    elif connection.vendor == 'mysql':
        schema_editor.execute(
            """
            UPDATE patchwork_seriesreference, patchwork_series
              SET patchwork_seriesreference.project_id = patchwork_series.project_id
            WHERE patchwork_seriesreference.series_id = patchwork_series.id
            """  # noqa
        )
    else:
        SeriesReference = apps.get_model('patchwork', 'SeriesReference')

        for series_ref in SeriesReference.objects.all().select_related(
            'series'
        ):
            series_ref.project = series_ref.series.project
            series_ref.save()


def delete_duplicate_series(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute(
            """
            DELETE
            FROM
              patchwork_seriesreference a
                USING patchwork_seriesreference b
            WHERE
              a.id < b.id
              AND a.project_id = b.project_id
              AND a.msgid = b.msgid
            """
        )
    elif connection.vendor == 'mysql':
        schema_editor.execute(
            """
            DELETE a FROM patchwork_seriesreference a
            INNER JOIN patchwork_seriesreference b
            WHERE
              a.id < b.id
              AND a.project_id = b.project_id
              AND a.msgid = b.msgid
            """
        )
    else:
        Project = apps.get_model('patchwork', 'Project')
        SeriesReference = apps.get_model('patchwork', 'SeriesReference')

        for project in Project.objects.all():
            (
                SeriesReference.objects.filter(project=project)
                .annotate(count=Count('msgid'))
                .filter(count__gt=1)
                .delete()
            )


class Migration(migrations.Migration):

    dependencies = [('patchwork', '0038_state_slug')]

    operations = [
        migrations.AddField(
            model_name='seriesreference',
            name='project',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.RunPython(
            copy_project_field, migrations.RunPython.noop, atomic=False
        ),
        migrations.RunPython(
            delete_duplicate_series, migrations.RunPython.noop, atomic=False
        ),
        migrations.AlterField(
            model_name='seriesreference',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='seriesreference', unique_together={('project', 'msgid')}
        ),
    ]
