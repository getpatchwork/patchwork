import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0022_add_subject_match_to_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='comment',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='emailconfirmation',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='event',
            name='date',
            field=models.DateTimeField(
                default=datetime.datetime.utcnow,
                help_text=b'The time this event was created.',
            ),
        ),
        migrations.AlterField(
            model_name='patchchangenotification',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AlterField(
            model_name='submission',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
    ]
