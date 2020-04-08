from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0020_tag_show_column'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='series',
            options={'ordering': ('date',), 'verbose_name_plural': 'Series'},
        ),
    ]

    operations += [
        migrations.AlterModelOptions(
            name='patch',
            options={
                'base_manager_name': 'objects',
                'verbose_name_plural': 'Patches',
            },
        ),
    ]
