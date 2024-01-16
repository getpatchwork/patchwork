from django.db import migrations, models
from django.utils import timezone as tz_utils


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0022_add_subject_match_to_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='date',
            field=models.DateTimeField(default=tz_utils.now),
        ),
        migrations.AlterField(
            model_name='comment',
            name='date',
            field=models.DateTimeField(default=tz_utils.now),
        ),
        migrations.AlterField(
            model_name='emailconfirmation',
            name='date',
            field=models.DateTimeField(default=tz_utils.now),
        ),
        migrations.AlterField(
            model_name='event',
            name='date',
            field=models.DateTimeField(
                default=tz_utils.now,
                help_text=b'The time this event was created.',
            ),
        ),
        migrations.AlterField(
            model_name='patchchangenotification',
            name='last_modified',
            field=models.DateTimeField(default=tz_utils.now),
        ),
        migrations.AlterField(
            model_name='submission',
            name='date',
            field=models.DateTimeField(default=tz_utils.now),
        ),
    ]
