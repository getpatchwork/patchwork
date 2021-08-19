# commit 3a979ed8bfc6 ("migrations: don't go to the db for 0041_python3 migration")
# made a bunch of strings go past 79 characters, breaking flake8 checks.
#
# We're not really expecting future changes to this file so just don't run
# flake8 against it.
#
# flake8: noqa

import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import patchwork.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('patchwork', '0040_add_related_patches'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='check',
                    name='context',
                    field=models.SlugField(
                        default='default',
                        help_text='A label to discern check from checks of other '
                                  'testing systems.',
                        max_length=255,
                    ),
                ),
                migrations.AlterField(
                    model_name='check',
                    name='description',
                    field=models.TextField(
                        blank=True,
                        help_text='A brief description of the check.',
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='check',
                    name='state',
                    field=models.SmallIntegerField(
                        choices=[
                            (0, 'pending'),
                            (1, 'success'),
                            (2, 'warning'),
                            (3, 'fail'),
                        ],
                        default=0,
                        help_text='The state of the check.',
                    ),
                ),
                migrations.AlterField(
                    model_name='check',
                    name='target_url',
                    field=models.URLField(
                        blank=True,
                        help_text='The target URL to associate with this check. This '
                                  'should be specific to the patch.',
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='comment',
                    name='submission',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        related_query_name='comment',
                        to='patchwork.Submission',
                    ),
                ),
                migrations.AlterField(
                    model_name='delegationrule',
                    name='path',
                    field=models.CharField(
                        help_text='An fnmatch-style pattern to match filenames '
                                  'against.',
                        max_length=255,
                    ),
                ),
                migrations.AlterField(
                    model_name='delegationrule',
                    name='priority',
                    field=models.IntegerField(
                        default=0,
                        help_text='The priority of the rule. Rules with a higher '
                                  'priority will override rules with lower priorities',
                    ),
                ),
                migrations.AlterField(
                    model_name='delegationrule',
                    name='user',
                    field=models.ForeignKey(
                        help_text='A user to delegate the patch to.',
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name='emailconfirmation',
                    name='type',
                    field=models.CharField(
                        choices=[
                            ('userperson', 'User-Person association'),
                            ('registration', 'Registration'),
                            ('optout', 'Email opt-out'),
                        ],
                        max_length=20,
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='actor',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='The user that caused/created this event.',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='category',
                    field=models.CharField(
                        choices=[
                            ('cover-created', 'Cover Letter Created'),
                            ('patch-created', 'Patch Created'),
                            ('patch-completed', 'Patch Completed'),
                            ('patch-state-changed', 'Patch State Changed'),
                            ('patch-delegated', 'Patch Delegate Changed'),
                            ('patch-relation-changed', 'Patch Relation Changed'),
                            ('check-created', 'Check Created'),
                            ('series-created', 'Series Created'),
                            ('series-completed', 'Series Completed'),
                        ],
                        db_index=True,
                        help_text='The category of the event.',
                        max_length=25,
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='cover',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='The cover letter that this event was created for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.CoverLetter',
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='date',
                    field=models.DateTimeField(
                        default=datetime.datetime.utcnow,
                        help_text='The time this event was created.',
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='patch',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='The patch that this event was created for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Patch',
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='project',
                    field=models.ForeignKey(
                        help_text='The project that the events belongs to.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Project',
                    ),
                ),
                migrations.AlterField(
                    model_name='event',
                    name='series',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='The series that this event was created for.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.Series',
                    ),
                ),
                migrations.AlterField(
                    model_name='patch',
                    name='number',
                    field=models.PositiveSmallIntegerField(
                        default=None,
                        help_text='The number assigned to this patch in the series',
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='commit_url_format',
                    field=models.CharField(
                        blank=True,
                        help_text='URL format for a particular commit. {} will be '
                                  'replaced by the commit SHA.',
                        max_length=2000,
                    ),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='list_archive_url_format',
                    field=models.CharField(
                        blank=True,
                        help_text="URL format for the list archive's Message-ID "
                                  "redirector. {} will be replaced by the Message-ID.",
                        max_length=2000,
                    ),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='subject_match',
                    field=models.CharField(
                        blank=True,
                        default='',
                        help_text='Regex to match the subject against if only part '
                                  'of emails sent to the list belongs to this project. Will be '
                                  'used with IGNORECASE and MULTILINE flags. If rules for more '
                                  'projects match the first one returned from DB is chosen; '
                                  'empty field serves as a default for every email which has no '
                                  'other match.',
                        max_length=64,
                        validators=[patchwork.models.validate_regex_compiles],
                    ),
                ),
                migrations.AlterField(
                    model_name='series',
                    name='name',
                    field=models.CharField(
                        blank=True,
                        help_text='An optional name to associate with the series, '
                                  'e.g. "John\'s PCI series".',
                        max_length=255,
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='series',
                    name='total',
                    field=models.IntegerField(
                        help_text='Number of patches in series as indicated by the '
                                  'subject prefix(es)'
                    ),
                ),
                migrations.AlterField(
                    model_name='series',
                    name='version',
                    field=models.IntegerField(
                        default=1,
                        help_text='Version of series as indicated by the subject '
                                  'prefix(es)',
                    ),
                ),
                migrations.AlterField(
                    model_name='seriesreference',
                    name='series',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='references',
                        related_query_name='reference',
                        to='patchwork.Series',
                    ),
                ),
                migrations.AlterField(
                    model_name='tag',
                    name='abbrev',
                    field=models.CharField(
                        help_text='Short (one-or-two letter) abbreviation for the '
                                  'tag, used in table column headers',
                        max_length=2,
                        unique=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='tag',
                    name='pattern',
                    field=models.CharField(
                        help_text='A simple regex to match the tag in the content of '
                                  'a message. Will be used with MULTILINE and IGNORECASE flags. '
                                  'eg. ^Acked-by:',
                        max_length=50,
                        validators=[patchwork.models.validate_regex_compiles],
                    ),
                ),
                migrations.AlterField(
                    model_name='tag',
                    name='show_column',
                    field=models.BooleanField(
                        default=True,
                        help_text="Show a column displaying this tag's count in the "
                                  "patch list view",
                    ),
                ),
                migrations.AlterField(
                    model_name='userprofile',
                    name='items_per_page',
                    field=models.PositiveIntegerField(
                        default=100, help_text='Number of items to display per page'
                    ),
                ),
                migrations.AlterField(
                    model_name='userprofile',
                    name='send_email',
                    field=models.BooleanField(
                        default=False,
                        help_text='Selecting this option allows patchwork to send '
                                  'email on your behalf',
                    ),
                ),
                migrations.AlterField(
                    model_name='userprofile',
                    name='show_ids',
                    field=models.BooleanField(
                        default=False,
                        help_text='Show click-to-copy patch IDs in the list view',
                    ),
                ),
            ],
        ),
    ]
