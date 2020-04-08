from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    # per migration 16, but note this seems to be going away
    # in new PostgreSQLs
    # https://stackoverflow.com/q/12838111#comment44629663_12838113
    atomic = False

    dependencies = [
        ('patchwork', '0023_timezone_unify'),
    ]

    operations = [
        migrations.AddField(
            model_name='patch',
            name='patch_project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
            preserve_default=False,
        ),
        # as with 10, this will break if you use non-default table names
        migrations.RunSQL(
            '''UPDATE patchwork_patch SET patch_project_id =
                               (SELECT project_id FROM patchwork_submission
                                WHERE patchwork_submission.id =
                                        patchwork_patch.submission_ptr_id);'''
        ),
        migrations.AlterField(
            model_name='patch',
            name='patch_project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
    ]
