from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0027_remove_series_ordering'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['submission', 'date'], name='submission_date_idx'
            ),
        ),
    ]
