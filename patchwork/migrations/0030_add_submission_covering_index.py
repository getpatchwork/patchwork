from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0029_add_list_covering_index'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(
                fields=['date', 'project', 'submitter', 'name'],
                name='submission_covering_idx',
            ),
        ),
    ]
