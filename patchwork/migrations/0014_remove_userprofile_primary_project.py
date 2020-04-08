from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0013_slug_check_context'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile', name='primary_project',
        ),
    ]
