from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0035_project_list_archive_url_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='commit_url_format',
            field=models.CharField(
                blank=True,
                help_text=b'URL format for a particular commit. {} will be '
                          b'replaced by the commit SHA.',
                max_length=2000,
            ),
        ),
    ]
