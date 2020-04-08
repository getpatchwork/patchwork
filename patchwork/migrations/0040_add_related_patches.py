from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0039_unique_series_references'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatchRelation',
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
            ],
        ),
        migrations.AlterField(
            model_name='event',
            name='category',
            field=models.CharField(
                choices=[
                    (b'cover-created', b'Cover Letter Created'),
                    (b'patch-created', b'Patch Created'),
                    (b'patch-completed', b'Patch Completed'),
                    (b'patch-state-changed', b'Patch State Changed'),
                    (b'patch-delegated', b'Patch Delegate Changed'),
                    (b'patch-relation-changed', b'Patch Relation Changed'),
                    (b'check-created', b'Check Created'),
                    (b'series-created', b'Series Created'),
                    (b'series-completed', b'Series Completed'),
                ],
                db_index=True,
                help_text=b'The category of the event.',
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='current_relation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.PatchRelation',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='previous_relation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.PatchRelation',
            ),
        ),
        migrations.AddField(
            model_name='patch',
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
    ]
