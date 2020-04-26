import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.migrations.operations.special
import django.db.models.deletion

import patchwork.fields
import patchwork.models


class Migration(migrations.Migration):

    replaces = [
        ('patchwork', '0001_initial'),
        ('patchwork', '0002_fix_patch_state_default_values'),
        ('patchwork', '0003_add_check_model'),
        ('patchwork', '0004_add_delegation_rule_model'),
        ('patchwork', '0005_unselectable_maintainer_projects'),
        ('patchwork', '0006_add_patch_diff'),
        ('patchwork', '0007_move_comment_content_to_patch_content'),
        ('patchwork', '0008_add_email_mixin'),
        ('patchwork', '0009_add_submission_model'),
        ('patchwork', '0010_migrate_data_from_submission_to_patch'),
        ('patchwork', '0011_remove_temp_fields'),
        ('patchwork', '0012_add_coverletter_model'),
        ('patchwork', '0013_slug_check_context'),
        ('patchwork', '0014_remove_userprofile_primary_project'),
        ('patchwork', '0015_add_series_models'),
        ('patchwork', '0016_series_project'),
        ('patchwork', '0017_improved_delegation_rule_docs'),
        ('patchwork', '0018_add_event_model'),
        ('patchwork', '0019_userprofile_show_ids'),
        ('patchwork', '0020_tag_show_column'),
        ('patchwork', '0021_django_1_10_fixes'),
        ('patchwork', '0022_add_subject_match_to_project'),
        ('patchwork', '0023_timezone_unify'),
        ('patchwork', '0024_patch_patch_project'),
        ('patchwork', '0025_add_regex_validators'),
        ('patchwork', '0026_add_user_bundles_backref'),
        ('patchwork', '0027_remove_series_ordering'),
        ('patchwork', '0028_add_comment_date_index'),
        ('patchwork', '0029_add_list_covering_index'),
        ('patchwork', '0030_add_submission_covering_index'),
        ('patchwork', '0031_add_patch_series_fields'),
        ('patchwork', '0032_migrate_data_from_series_patch_to_patch'),
        ('patchwork', '0033_remove_patch_series_model'),
        ('patchwork', '0034_project_list_archive_url'),
        ('patchwork', '0035_project_list_archive_url_format'),
        ('patchwork', '0036_project_commit_url_format'),
        ('patchwork', '0037_event_actor'),
        ('patchwork', '0038_state_slug'),
        ('patchwork', '0039_unique_series_references'),
        ('patchwork', '0040_add_related_patches'),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bundle',
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
                ('name', models.CharField(max_length=50)),
                ('public', models.BooleanField(default=False)),
                (
                    'owner',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bundles',
                        related_query_name='bundle',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Check',
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
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                (
                    'state',
                    models.SmallIntegerField(
                        choices=[
                            (0, b'pending'),
                            (1, b'success'),
                            (2, b'warning'),
                            (3, b'fail'),
                        ],
                        default=0,
                        help_text=b'The state of the check.',
                    ),
                ),
                (
                    'target_url',
                    models.URLField(
                        blank=True,
                        help_text=b'The target URL to associate with this '
                                  b'check. This should be specific to the '
                                  b'patch.',
                        null=True,
                    ),
                ),
                (
                    'description',
                    models.TextField(
                        blank=True,
                        help_text=b'A brief description of the check.',
                        null=True,
                    ),
                ),
                (
                    'context',
                    models.SlugField(
                        default='default',
                        help_text=b'A label to discern check from checks of '
                                  b'other testing systems.',
                        max_length=255,
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
        ),
        migrations.CreateModel(
            name='EmailOptout',
            fields=[
                (
                    'email',
                    models.CharField(
                        max_length=200, primary_key=True, serialize=False
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='PatchRelation',
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
            ],
        ),
        migrations.CreateModel(
            name='Person',
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
                ('email', models.CharField(max_length=255, unique=True)),
                (
                    'name',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'verbose_name_plural': 'People'},
        ),
        migrations.CreateModel(
            name='Project',
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
                ('linkname', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('listid', models.CharField(max_length=255)),
                ('listemail', models.CharField(max_length=200)),
                (
                    'subject_match',
                    models.CharField(
                        blank=True,
                        default='',
                        help_text=b'Regex to match the subject against if '
                                  b'only part of emails sent to the list '
                                  b'belongs to this project. Will be used '
                                  b'with IGNORECASE and MULTILINE flags. If '
                                  b'rules for more projects match the first '
                                  b'one returned from DB is chosen; empty '
                                  b'field serves as a default for every email '
                                  b'which has no other match.',
                        max_length=64,
                        validators=[patchwork.models.validate_regex_compiles],
                    ),
                ),
                ('web_url', models.CharField(blank=True, max_length=2000)),
                ('scm_url', models.CharField(blank=True, max_length=2000)),
                ('webscm_url', models.CharField(blank=True, max_length=2000)),
                (
                    'list_archive_url',
                    models.CharField(blank=True, max_length=2000),
                ),
                (
                    'list_archive_url_format',
                    models.CharField(
                        blank=True,
                        help_text=b"URL format for the list archive's "
                                  b"Message-ID redirector. {} will be "
                                  b"replaced by the Message-ID.",
                        max_length=2000,
                    ),
                ),
                (
                    'commit_url_format',
                    models.CharField(
                        blank=True,
                        help_text=b'URL format for a particular commit. {} '
                                  b'will be replaced by the commit SHA.',
                        max_length=2000,
                    ),
                ),
                ('send_notifications', models.BooleanField(default=False)),
                ('use_tags', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['linkname'],
                'unique_together': {('listid', 'subject_match')},
            },
        ),
        migrations.CreateModel(
            name='Series',
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
                    'name',
                    models.CharField(
                        blank=True,
                        help_text=b'An optional name to associate with the '
                                  b'series, e.g. "John\'s PCI series".',
                        max_length=255,
                        null=True,
                    ),
                ),
                ('date', models.DateTimeField()),
                (
                    'version',
                    models.IntegerField(
                        default=1,
                        help_text=b'Version of series as indicated by the '
                                  b'subject prefix(es)',
                    ),
                ),
                (
                    'total',
                    models.IntegerField(
                        help_text=b'Number of patches in series as indicated '
                                  b'by the subject prefix(es)'
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='series',
                        to='patchwork.Project',
                    ),
                ),
                (
                    'submitter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Person',
                    ),
                ),
            ],
            options={'verbose_name_plural': 'Series'},
            bases=(patchwork.models.FilenameMixin, models.Model),
        ),
        migrations.CreateModel(
            name='State',
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
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('ordering', models.IntegerField(unique=True)),
                ('action_required', models.BooleanField(default=True)),
            ],
            options={'ordering': ['ordering']},
        ),
        migrations.CreateModel(
            name='Submission',
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
                ('msgid', models.CharField(max_length=255)),
                (
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('name', models.CharField(max_length=255)),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Project',
                    ),
                ),
                (
                    'submitter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Person',
                    ),
                ),
            ],
            options={'ordering': ['date']},
            bases=(patchwork.models.FilenameMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Tag',
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
                ('name', models.CharField(max_length=20)),
                (
                    'pattern',
                    models.CharField(
                        help_text=b'A simple regex to match the tag in the '
                                  b'content of a message. Will be used with '
                                  b'MULTILINE and IGNORECASE flags. eg. '
                                  b'^Acked-by:',
                        max_length=50,
                        validators=[patchwork.models.validate_regex_compiles],
                    ),
                ),
                (
                    'abbrev',
                    models.CharField(
                        help_text=b'Short (one-or-two letter) abbreviation '
                                  b'for the tag, used in table column headers',
                        max_length=2,
                        unique=True,
                    ),
                ),
                (
                    'show_column',
                    models.BooleanField(
                        default=True,
                        help_text=b"Show a column displaying this tag's count "
                                  b"in the patch list view",
                    ),
                ),
            ],
            options={'ordering': ['abbrev']},
        ),
        migrations.CreateModel(
            name='CoverLetter',
            fields=[
                (
                    'submission_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='patchwork.Submission',
                    ),
                ),
            ],
            options={'abstract': False},
            bases=('patchwork.submission',),
        ),
        migrations.CreateModel(
            name='Patch',
            fields=[
                (
                    'submission_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='patchwork.Submission',
                    ),
                ),
                ('diff', models.TextField(blank=True, null=True)),
                (
                    'commit_ref',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    'pull_url',
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ('archived', models.BooleanField(default=False)),
                (
                    'hash',
                    patchwork.fields.HashField(
                        blank=True, max_length=40, null=True
                    ),
                ),
                (
                    'number',
                    models.PositiveSmallIntegerField(
                        default=None,
                        help_text=b'The number assigned to this patch in the '
                                  b'series',
                        null=True,
                    ),
                ),
            ],
            options={
                'verbose_name_plural': 'Patches',
                'base_manager_name': 'objects',
            },
            bases=('patchwork.submission',),
        ),
        migrations.CreateModel(
            name='UserProfile',
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
                    'send_email',
                    models.BooleanField(
                        default=False,
                        help_text=b'Selecting this option allows patchwork to '
                                  b'send email on your behalf',
                    ),
                ),
                (
                    'items_per_page',
                    models.PositiveIntegerField(
                        default=100,
                        help_text=b'Number of items to display per page',
                    ),
                ),
                (
                    'show_ids',
                    models.BooleanField(
                        default=False,
                        help_text=b'Show click-to-copy patch IDs in the list '
                                  b'view',
                    ),
                ),
                (
                    'maintainer_projects',
                    models.ManyToManyField(
                        blank=True,
                        related_name='maintainer_project',
                        to='patchwork.Project',
                    ),
                ),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='profile',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='SeriesReference',
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
                ('msgid', models.CharField(max_length=255)),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Project',
                    ),
                ),
                (
                    'series',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='references',
                        related_query_name=b'reference',
                        to='patchwork.Series',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='PatchTag',
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
                ('count', models.IntegerField(default=1)),
                (
                    'tag',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Tag',
                    ),
                ),
            ],
        ),
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
                            (b'patch-relation-changed', b'Patch Relation Changed'),  # noqa
                            (b'check-created', b'Check Created'),
                            (b'series-created', b'Series Created'),
                            (b'series-completed', b'Series Completed'),
                        ],
                        db_index=True,
                        help_text=b'The category of the event.',
                        max_length=25,
                    ),
                ),
                (
                    'date',
                    models.DateTimeField(
                        default=datetime.datetime.utcnow,
                        help_text=b'The time this event was created.',
                    ),
                ),
                (
                    'actor',
                    models.ForeignKey(
                        blank=True,
                        help_text=b'The user that caused/created this event.',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
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
                    'current_relation',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.PatchRelation',
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
                    'previous_relation',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='patchwork.PatchRelation',
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
        migrations.CreateModel(
            name='EmailConfirmation',
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
                    'type',
                    models.CharField(
                        choices=[
                            (b'userperson', b'User-Person association'),
                            (b'registration', b'Registration'),
                            (b'optout', b'Email opt-out'),
                        ],
                        max_length=20,
                    ),
                ),
                ('email', models.CharField(max_length=200)),
                ('key', patchwork.fields.HashField(max_length=40)),
                (
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                ('active', models.BooleanField(default=True)),
                (
                    'user',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='DelegationRule',
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
                    'path',
                    models.CharField(
                        help_text=b'An fnmatch-style pattern to match '
                                  b'filenames against.',
                        max_length=255,
                    ),
                ),
                (
                    'priority',
                    models.IntegerField(
                        default=0,
                        help_text=b'The priority of the rule. Rules with a '
                                  b'higher priority will override rules with '
                                  b'lower priorities',
                    ),
                ),
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
                        help_text=b'A user to delegate the patch to.',
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'ordering': ['-priority', 'path']},
        ),
        migrations.CreateModel(
            name='Comment',
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
                ('msgid', models.CharField(max_length=255)),
                (
                    'date',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField(blank=True, null=True)),
                (
                    'submission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='comments',
                        related_query_name=b'comment',
                        to='patchwork.Submission',
                    ),
                ),
                (
                    'submitter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Person',
                    ),
                ),
            ],
            options={'ordering': ['date']},
        ),
        migrations.CreateModel(
            name='BundlePatch',
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
                ('order', models.IntegerField()),
                (
                    'bundle',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.Bundle',
                    ),
                ),
            ],
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='bundle',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.CreateModel(
            name='PatchChangeNotification',
            fields=[
                (
                    'patch',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to='patchwork.Patch',
                    ),
                ),
                (
                    'last_modified',
                    models.DateTimeField(default=datetime.datetime.utcnow),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(
                fields=['date', 'project', 'submitter', 'name'],
                name='submission_covering_idx',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='submission', unique_together={('msgid', 'project')},
        ),
        migrations.AlterUniqueTogether(
            name='seriesreference', unique_together={('project', 'msgid')},
        ),
        migrations.AddField(
            model_name='series',
            name='cover_letter',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='series',
                to='patchwork.CoverLetter',
            ),
        ),
        migrations.AddField(
            model_name='patchtag',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='delegate',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='patch_project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='related',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='patches',
                related_query_name='patch',
                to='patchwork.PatchRelation',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='series',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='patches',
                related_query_name='patch',
                to='patchwork.Series',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='state',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.State',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='tags',
            field=models.ManyToManyField(
                through='patchwork.PatchTag', to='patchwork.Tag'
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='cover',
            field=models.ForeignKey(
                blank=True,
                help_text=b'The cover letter that this event was created for.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.CoverLetter',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='patch',
            field=models.ForeignKey(
                blank=True,
                help_text=b'The patch that this event was created for.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='patchwork.Patch',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='delegationrule', unique_together={('path', 'project')},
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['submission', 'date'], name='submission_date_idx'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='comment', unique_together={('msgid', 'submission')},
        ),
        migrations.AddField(
            model_name='check',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AddField(
            model_name='bundlepatch',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AddField(
            model_name='bundle',
            name='patches',
            field=models.ManyToManyField(
                through='patchwork.BundlePatch', to='patchwork.Patch'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='patchtag', unique_together={('patch', 'tag')},
        ),
        migrations.AddField(
            model_name='patchchangenotification',
            name='orig_state',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.State',
            ),
        ),
        migrations.AddIndex(
            model_name='patch',
            index=models.Index(
                fields=['archived', 'patch_project', 'state', 'delegate'],
                name='patch_list_covering_idx',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='patch', unique_together={('series', 'number')},
        ),
        migrations.AlterUniqueTogether(
            name='bundlepatch', unique_together={('bundle', 'patch')},
        ),
        migrations.AlterUniqueTogether(
            name='bundle', unique_together={('owner', 'name')},
        ),
    ]
