from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0033_remove_patch_series_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='list_archive_url',
            field=models.CharField(blank=True, max_length=2000),
        ),
    ]
