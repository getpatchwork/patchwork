import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('patchwork', '0017_improved_delegation_rule_docs'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'category',
                    models.CharField(
                        choices=[
                            (b'cover-created', b'Cover Letter Created'),
                            (b'patch-created', b'Patch Created'),
                            (b'patch-completed', b'Patch Completed'),
                            (b'patch-state-changed', b'Patch State Changed'),
                            (b'patch-delegated', b'Patch Delegate Changed'),
                            (b'check-created', b'Check Created'),
                            (b'series-created', b'Series Created'),
                            (b'series-completed', b'Series Completed'),
                        ],
                        db_index=True,
                        help_text=b'The category of the event.',
                        max_length=20,
                    ),
                ),
                (
                    'date',
                    models.DateTimeField(
                        default=datetime.datetime.now,
                        help_text=b'The time this event was created.',
                    ),
                ),
                (
                    'cover',
                    models.ForeignKey(
                        blank=True,
                        help_text=b'The cover letter that this event was '
                                  b'created for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.CoverLetter',
                    ),
                ),
                (
                    'created_check',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Check',
                    ),
                ),
                (
                    'current_delegate',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'current_state',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.State',
                    ),
                ),
                (
                    'patch',
                    models.ForeignKey(
                        blank=True,
                        help_text=b'The patch that this event was created '
                                  b'for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Patch',
                    ),
                ),
                (
                    'previous_delegate',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'previous_state',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.State',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        help_text=b'The project that the events belongs to.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Project',
                    ),
                ),
                (
                    'series',
                    models.ForeignKey(
                        blank=True,
                        help_text=b'The series that this event was created '
                                  b'for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Series',
                    ),
                ),
            ],
            options={'ordering': ['-date']},
        ),
    ]
