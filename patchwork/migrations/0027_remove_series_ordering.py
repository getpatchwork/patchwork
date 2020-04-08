from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0026_add_user_bundles_backref'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='series', options={'verbose_name_plural': 'Series'},
        ),
    ]
