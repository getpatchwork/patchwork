import datetime

from django.db import connection, migrations, models
import django.db.models.deletion
import patchwork.models


def delete_coverletter_comments(apps, schema_editor):
    if connection.vendor == 'mysql':
        schema_editor.execute(
            """
            DELETE patchwork_comment FROM
                patchwork_comment
            INNER JOIN patchwork_coverletter
                ON patchwork_coverletter.submission_ptr_id = patchwork_comment.submission_id
            """,  # noqa
        )
    elif connection.vendor == 'postgresql':
        schema_editor.execute(
            """
            DELETE
            FROM patchwork_comment
                USING patchwork_coverletter
            WHERE patchwork_coverletter.submission_ptr_id = patchwork_comment.submission_id
            """,  # noqa
        )
    else:
        CoverLetter = apps.get_model('patchwork', 'CoverLetter')

        for cover in CoverLetter.objects.all():
            cover.comments.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0041_python3'),
    ]

    operations = [
        # create a new, separate cover (letter) model

        migrations.CreateModel(
            name='Cover',
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
                ('msgid', models.CharField(max_length=255)),
                (
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('name', models.CharField(max_length=255)),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Project',
                    ),
                ),
                (
                    'submitter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Person',
                    ),
                ),
            ],
            options={'ordering': ['date']},
            bases=(patchwork.models.FilenameMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name='cover',
            index=models.Index(
                fields=['date', 'project', 'submitter', 'name'],
                name='cover_covering_idx',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='cover', unique_together=set([('msgid', 'project')]),
        ),

        # create a new, separate cover (letter) comment model

        migrations.CreateModel(
            name='CoverComment',
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
                ('msgid', models.CharField(max_length=255)),
                (
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField(blank=True, null=True)),
                (
                    'cover',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        related_query_name='comment',
                        to='patchwork.Cover',
                    ),
                ),
                (
                    'submitter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Person',
                    ),
                ),
            ],
            options={'ordering': ['date']},
        ),
        migrations.AddIndex(
            model_name='covercomment',
            index=models.Index(
                fields=['cover', 'date'], name='cover_date_idx'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='covercomment', unique_together=set([('msgid', 'cover')]),
        ),

        # copy all entries from the 'CoverLetter' model to the new 'Cover'
        # model; note that it's not possible to reverse this since we can't
        # guarantee IDs will be unique after the split

        migrations.RunSQL(
            """
            INSERT INTO patchwork_cover
                (id, msgid, name, date, headers, project_id, submitter_id,
                 content)
            SELECT s.id, s.msgid, s.name, s.date, s.headers, s.project_id,
                s.submitter_id, s.content
            FROM patchwork_coverletter c
            INNER JOIN patchwork_submission s ON s.id = c.submission_ptr_id
            """,
            None,
        ),

        # copy all 'CoverLetter'-related comments to the new 'CoverComment'
        # table; as above, this is non-reversible

        migrations.RunSQL(
            """
            INSERT INTO patchwork_covercomment
                (id, msgid, date, headers, content, cover_id, submitter_id)
            SELECT c.id, c.msgid, c.date, c.headers, c.content,
                c.submission_id, c.submitter_id
            FROM patchwork_comment c
            INNER JOIN patchwork_coverletter p
                ON p.submission_ptr_id = c.submission_id
            """,
            None,
        ),

        # update all references to the 'CoverLetter' model to point to the new
        # 'Cover' model instead

        migrations.AlterField(
            model_name='event',
            name='cover',
            field=models.ForeignKey(
                blank=True,
                help_text='The cover letter that this event was created for.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.Cover',
            ),
        ),
        migrations.AlterField(
            model_name='series',
            name='cover_letter',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='series',
                to='patchwork.Cover'
            ),
        ),

        # remove all the old 'CoverLetter'-related entries from the 'Comment'
        # table

        migrations.RunPython(delete_coverletter_comments, None, atomic=False),

        # delete the old 'CoverLetter' model

        migrations.DeleteModel(
            name='CoverLetter',
        ),

        # rename the 'Comment.submission' field to 'Comment.patch'; note our
        # use of 'AlterField' before and after to work around bug #31335
        #
        # https://code.djangoproject.com/ticket/31335

        migrations.AlterField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                related_query_name='comment',
                to='patchwork.Submission',
            ),
        ),
        migrations.RemoveIndex(
            model_name='comment',
            name='submission_date_idx',
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='submission',
            new_name='patch',
        ),
        migrations.AlterUniqueTogether(
            name='comment',
            unique_together=set([('msgid', 'patch')]),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['patch', 'date'],
                name='patch_date_idx',
            ),
        ),
        migrations.AlterField(
            model_name='comment',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                related_query_name='comment',
                to='patchwork.Submission',
            ),
        ),

        # rename the 'Comment' model to 'PatchComment'

        migrations.RenameModel(
            old_name='Comment',
            new_name='PatchComment',
        ),
    ]
