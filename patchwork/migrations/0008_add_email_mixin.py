from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0007_move_comment_content_to_patch_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(null=True, blank=True),
        ),
    ]
