from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0028_add_comment_date_index'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='patch',
            index=models.Index(
                fields=['archived', 'patch_project', 'state', 'delegate'],
                name='patch_list_covering_idx',
            ),
        ),
    ]
