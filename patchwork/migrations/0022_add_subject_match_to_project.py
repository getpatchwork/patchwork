from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0021_django_1_10_fixes'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='subject_match',
            field=models.CharField(
                blank=True,
                default=b'',
                help_text=b'Regex to match the subject against if only part '
                          b'of emails sent to the list belongs to this '
                          b'project. Will be used with IGNORECASE and '
                          b'MULTILINE flags. If rules for more projects match '
                          b'the first one returned from DB is chosen; empty '
                          b'field serves as a default for every email which '
                          b'has no other match.',
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='listid',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='project', unique_together=set([('listid', 'subject_match')]),
        ),
    ]
