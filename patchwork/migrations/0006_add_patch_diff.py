from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0005_unselectable_maintainer_projects'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patch', old_name='content', new_name='diff',
        ),
        migrations.AddField(
            model_name='patch',
            name='content',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_query_name=b'comment',
                related_name='comments',
                to='patchwork.Patch',
            ),
        ),
    ]
