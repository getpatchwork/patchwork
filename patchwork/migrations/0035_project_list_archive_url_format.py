from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0034_project_list_archive_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='list_archive_url_format',
            field=models.CharField(
                blank=True,
                help_text=b"URL format for the list archive's Message-ID "
                          b"redirector. {} will be replaced by the "
                          b"Message-ID.",
                max_length=2000,
            ),
        ),
    ]
