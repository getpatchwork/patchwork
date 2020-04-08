from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0012_add_coverletter_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='context',
            field=models.SlugField(
                default=b'default',
                help_text=b'A label to discern check from checks of other '
                          b'testing systems.',
                max_length=255,
            ),
        ),
    ]
