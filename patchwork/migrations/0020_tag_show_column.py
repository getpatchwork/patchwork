from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0019_userprofile_show_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='show_column',
            field=models.BooleanField(
                default=True,
                help_text=b"Show a column displaying this tag's count in the "
                          b"patch list view",
            ),
        ),
    ]
