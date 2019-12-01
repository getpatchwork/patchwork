from django.db import connection, migrations, models
from django.db.models import Count
import django.db.models.deletion


def merge_duplicate_series(apps, schema_editor):
    SeriesReference = apps.get_model('patchwork', 'SeriesReference')
    Patch = apps.get_model('patchwork', 'Patch')

    msgid_seriesrefs = {}

    # find all SeriesReference that share a msgid but point to different series
    # and decide which of the series is going to be the authoritative one
    msgid_counts = (
        SeriesReference.objects.values('msgid')
        .annotate(count=Count('msgid'))
        .filter(count__gt=1)
    )
    for msgid_count in msgid_counts:
        msgid = msgid_count['msgid']
        chosen_ref = None
        for series_ref in SeriesReference.objects.filter(msgid=msgid):
            if series_ref.series.cover_letter:
                if chosen_ref:
                    # I don't think this can happen, but explode if it does
                    raise Exception(
                        "Looks like you've got two or more series that share "
                        "some patches but do not share a cover letter. Unable "
                        "to auto-resolve."
                    )

                # if a series has a cover letter, that's the one we'll group
                # everything under
                chosen_ref = series_ref

        if not chosen_ref:
            # if none of the series have cover letters, simply use the last
            # one (hint: this relies on Python's weird scoping for for loops
            # where 'series_ref' is still accessible outside the loop)
            chosen_ref = series_ref

        msgid_seriesrefs[msgid] = chosen_ref

    # reassign any patches referring to non-authoritative series to point to
    # the authoritative one, and delete the other series; we do this separately
    # to allow us a chance to raise the exception above if necessary
    for msgid, chosen_ref in msgid_seriesrefs.items():
        for series_ref in SeriesReference.objects.filter(msgid=msgid):
            if series_ref == chosen_ref:
                continue

            # update the patches to point to our chosen series instead, on the
            # assumption that all other metadata is correct
            for patch in Patch.objects.filter(series=series_ref.series):
                patch.series = chosen_ref.series
                patch.save()

            # delete the other series (which will delete the series ref)
            series_ref.series.delete()


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


class Migration(migrations.Migration):

    dependencies = [('patchwork', '0038_state_slug')]

    operations = [
        migrations.RunPython(
            merge_duplicate_series, migrations.RunPython.noop, atomic=False
        ),
        migrations.AddField(
            model_name='seriesreference',
            name='project',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='seriesreference', unique_together={('project', 'msgid')}
        ),
        migrations.RunPython(
            copy_project_field, migrations.RunPython.noop, atomic=False
        ),
        migrations.AlterField(
            model_name='seriesreference',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
    ]
