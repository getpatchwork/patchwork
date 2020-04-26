from django.conf import settings
from django.db import connection, migrations, models
import django.db.models.deletion

import patchwork.fields


def migrate_data(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute(
            """
            UPDATE patchwork_submission
              SET archived = patchwork_patch.archived2,
                  commit_ref = patchwork_patch.commit_ref2,
                  delegate_id = patchwork_patch.delegate2_id,
                  diff = patchwork_patch.diff2,
                  hash = patchwork_patch.hash2,
                  number = patchwork_patch.number2,
                  pull_url = patchwork_patch.pull_url2,
                  related_id = patchwork_patch.related2_id,
                  series_id = patchwork_patch.series2_id,
                  state_id = patchwork_patch.state2_id
            FROM patchwork_patch
              WHERE patchwork_submission.id = patchwork_patch.submission_ptr_id
            """
        )
    elif connection.vendor == 'mysql':
        schema_editor.execute(
            """
            UPDATE patchwork_submission, patchwork_patch
              SET patchwork_submission.archived = patchwork_patch.archived2,
                  patchwork_submission.commit_ref = patchwork_patch.commit_ref2,
                  patchwork_submission.delegate_id = patchwork_patch.delegate2_id,
                  patchwork_submission.diff = patchwork_patch.diff2,
                  patchwork_submission.hash = patchwork_patch.hash2,
                  patchwork_submission.number = patchwork_patch.number2,
                  patchwork_submission.pull_url = patchwork_patch.pull_url2,
                  patchwork_submission.related_id = patchwork_patch.related2_id,
                  patchwork_submission.series_id = patchwork_patch.series2_id,
                  patchwork_submission.state_id = patchwork_patch.state2_id
            WHERE patchwork_submission.id = patchwork_patch.submission_ptr_id
            """  # noqa
        )
    else:
        schema_editor.execute(
            """
            UPDATE patchwork_submission
              SET (
                archived, commit_ref, delegate_id, diff, hash, number,
                pull_url, related_id, series_id, state_id
              ) = (
                SELECT
                  patchwork_patch.archived2,
                  patchwork_patch.commit_ref2,
                  patchwork_patch.delegate2_id,
                  patchwork_patch.diff2,
                  patchwork_patch.hash2,
                  patchwork_patch.number2,
                  patchwork_patch.pull_url2,
                  patchwork_patch.related2_id,
                  patchwork_patch.series2_id,
                  patchwork_patch.state2_id
                FROM patchwork_patch
                WHERE patchwork_patch.submission_ptr_id = patchwork_submission.id
              )
            WHERE
              EXISTS (
                SELECT *
                FROM patchwork_patch
                WHERE patchwork_patch.submission_ptr_id = patchwork_submission.id
              )
            """  # noqa
        )


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('patchwork', '0042_add_cover_model'),
    ]

    operations = [
        # move the 'PatchTag' model to point to 'Submission'

        migrations.RemoveField(model_name='patch', name='tags',),
        migrations.AddField(
            model_name='submission',
            name='tags',
            field=models.ManyToManyField(
                through='patchwork.PatchTag', to='patchwork.Tag'
            ),
        ),
        migrations.AlterField(
            model_name='patchtag',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Submission',
            ),
        ),

        # do the same for any other field that references 'Patch'

        migrations.AlterField(
            model_name='bundle',
            name='patches',
            field=models.ManyToManyField(
                through='patchwork.BundlePatch', to='patchwork.Submission'
            ),
        ),
        migrations.AlterField(
            model_name='bundlepatch',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Submission',
            ),
        ),
        migrations.AlterField(
            model_name='check',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Submission',
            ),
        ),
        migrations.AlterField(
            model_name='event',
            name='patch',
            field=models.ForeignKey(
                blank=True,
                help_text='The patch that this event was created for.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.Submission',
            ),
        ),
        migrations.AlterField(
            model_name='patchchangenotification',
            name='patch',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                serialize=False,
                to='patchwork.Submission',
            ),
        ),

        # rename all the fields on 'Patch' so we don't have duplicates when we
        # add them to 'Submission'

        migrations.RemoveIndex(
            model_name='patch', name='patch_list_covering_idx',
        ),
        migrations.AlterUniqueTogether(name='patch', unique_together=set([]),),
        migrations.RenameField(
            model_name='patch', old_name='archived', new_name='archived2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='commit_ref', new_name='commit_ref2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='delegate', new_name='delegate2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='diff', new_name='diff2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='hash', new_name='hash2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='number', new_name='number2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='pull_url', new_name='pull_url2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='related', new_name='related2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='series', new_name='series2',
        ),
        migrations.RenameField(
            model_name='patch', old_name='state', new_name='state2',
        ),

        # add the fields found on 'Patch' to 'Submission'

        migrations.AddField(
            model_name='submission',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='submission',
            name='commit_ref',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='delegate',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='submission',
            name='diff',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='hash',
            field=patchwork.fields.HashField(
                blank=True, max_length=40, null=True
            ),
        ),
        migrations.AddField(
            model_name='submission',
            name='number',
            field=models.PositiveSmallIntegerField(
                default=None,
                help_text='The number assigned to this patch in the series',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='submission',
            name='pull_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='related',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='patches',
                related_query_name='patch',
                to='patchwork.PatchRelation',
            ),
        ),
        migrations.AddField(
            model_name='submission',
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
        migrations.AddField(
            model_name='submission',
            name='state',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.State',
            ),
        ),

        # copy the data from 'Patch' to 'Submission'

        migrations.RunPython(migrate_data, None, atomic=False),

        # configure metadata for the 'Submission' model

        migrations.AlterModelOptions(
            name='submission',
            options={
                'base_manager_name': 'objects',
                'ordering': ['date'],
                'verbose_name_plural': 'Patches',
            },
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('series', 'number'), ('msgid', 'project')]),
        ),
        migrations.RemoveIndex(
            model_name='submission', name='submission_covering_idx',
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(
                fields=[
                    'archived',
                    'state',
                    'delegate',
                    'date',
                    'project',
                    'submitter',
                    'name',
                ],
                name='patch_covering_idx',
            ),
        ),

        # remove the foreign key fields from the 'Patch' model

        migrations.RemoveField(model_name='patch', name='delegate2',),
        migrations.RemoveField(model_name='patch', name='patch_project',),
        migrations.RemoveField(model_name='patch', name='related2',),
        migrations.RemoveField(model_name='patch', name='series2',),
        migrations.RemoveField(model_name='patch', name='state2',),
        migrations.RemoveField(model_name='patch', name='submission_ptr',),

        # drop the 'Patch' model and rename 'Submission' to 'Patch'

        migrations.DeleteModel(name='Patch',),
        migrations.RenameModel(old_name='Submission', new_name='Patch',),
    ]
