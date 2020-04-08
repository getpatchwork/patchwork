from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0011_remove_temp_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoverLetter',
            fields=[
                (
                    'submission_ptr',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to='patchwork.Submission',
                    ),
                ),
            ],
            options={'abstract': False},
            bases=('patchwork.submission',),
        ),
    ]
