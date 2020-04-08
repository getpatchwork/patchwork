from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0010_migrate_data_from_submission_to_patch'),
    ]

    operations = [
        # Remove duplicate fields from 'Submission' and rename 'Patch' version
        migrations.RemoveField(model_name='submission', name='diff',),
        migrations.RenameField(
            model_name='patch', old_name='diff2', new_name='diff',
        ),
        migrations.RemoveField(model_name='submission', name='commit_ref',),
        migrations.RenameField(
            model_name='patch', old_name='commit_ref2', new_name='commit_ref',
        ),
        migrations.RemoveField(model_name='submission', name='pull_url',),
        migrations.RenameField(
            model_name='patch', old_name='pull_url2', new_name='pull_url',
        ),
        migrations.RemoveField(model_name='submission', name='tags',),
        migrations.RenameField(
            model_name='patch', old_name='tags2', new_name='tags',
        ),
        migrations.RemoveField(model_name='submission', name='delegate',),
        migrations.RenameField(
            model_name='patch', old_name='delegate2', new_name='delegate',
        ),
        migrations.RemoveField(model_name='submission', name='state',),
        migrations.RenameField(
            model_name='patch', old_name='state2', new_name='state',
        ),
        migrations.RemoveField(model_name='submission', name='archived',),
        migrations.RenameField(
            model_name='patch', old_name='archived2', new_name='archived',
        ),
        migrations.RemoveField(model_name='submission', name='hash',),
        migrations.RenameField(
            model_name='patch', old_name='hash2', new_name='hash',
        ),
        # Update any many-to-many fields to point to Patch now
        migrations.AlterField(
            model_name='bundle',
            name='patches',
            field=models.ManyToManyField(
                to='patchwork.Patch', through='patchwork.BundlePatch'
            ),
        ),
        migrations.AlterField(
            model_name='bundlepatch',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AlterField(
            model_name='check',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AlterField(
            model_name='patch',
            name='state',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.State',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='patchchangenotification',
            name='patch',
            field=models.OneToOneField(
                primary_key=True,
                serialize=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AlterField(
            model_name='patchtag',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
    ]
