from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('patchwork', '0003_add_check_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='DelegationRule',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('path', models.CharField(max_length=255)),
                ('priority', models.IntegerField(default=0)),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Project',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'ordering': ['-priority', 'path']},
        ),
        migrations.AlterUniqueTogether(
            name='delegationrule', unique_together=set([('path', 'project')]),
        ),
    ]
