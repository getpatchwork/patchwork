from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0018_add_event_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='show_ids',
            field=models.BooleanField(
                default=False,
                help_text=b'Show click-to-copy patch IDs in the list view',
            ),
        ),
    ]
