from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0045_addressed_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='cover_comment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.covercomment',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='patch_comment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.patchcomment',
            ),
        ),
        migrations.AlterField(
            model_name='event',
            name='category',
            field=models.CharField(
                choices=[
                    ('cover-created', 'Cover Letter Created'),
                    ('patch-created', 'Patch Created'),
                    ('patch-completed', 'Patch Completed'),
                    ('patch-state-changed', 'Patch State Changed'),
                    ('patch-delegated', 'Patch Delegate Changed'),
                    ('patch-relation-changed', 'Patch Relation Changed'),
                    ('check-created', 'Check Created'),
                    ('series-created', 'Series Created'),
                    ('series-completed', 'Series Completed'),
                    ('cover-comment-created', 'Cover Comment Created'),
                    ('patch-comment-created', 'Patch Comment Created'),
                ],
                db_index=True,
                help_text='The category of the event.',
                max_length=25,
            ),
        ),
    ]
