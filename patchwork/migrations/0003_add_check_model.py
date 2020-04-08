import datetime

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('patchwork', '0002_fix_patch_state_default_values'),
    ]

    operations = [
        migrations.CreateModel(
            name='Check',
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
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                (
                    'state',
                    models.SmallIntegerField(
                        default=0,
                        help_text=b'The state of the check.',
                        choices=[
                            (0, b'pending'),
                            (1, b'success'),
                            (2, b'warning'),
                            (3, b'fail'),
                        ],
                    ),
                ),
                (
                    'target_url',
                    models.URLField(
                        help_text=b'The target URL to associate with this '
                                  b'check. This should be specific to the '
                                  b'patch.',
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    'description',
                    models.TextField(
                        help_text=b'A brief description of the check.',
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    'context',
                    models.CharField(
                        default=b'default',
                        max_length=255,
                        null=True,
                        help_text=b'A label to discern check from checks of '
                                  b'other testing systems.',
                        blank=True,
                    ),
                ),
                (
                    'patch',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Patch',
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
            options={},
            bases=(models.Model,),
        ),
    ]
