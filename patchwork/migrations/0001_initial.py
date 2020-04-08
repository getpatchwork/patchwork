import datetime

from django.conf import settings
from django.db import models, migrations
import django.db.models.deletion

import patchwork.models


class Migration(migrations.Migration):

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
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('name', models.CharField(max_length=50)),
                ('public', models.BooleanField(default=False)),
                (
                    'owner',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='BundlePatch',
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
        migrations.CreateModel(
            name='Comment',
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
                ('msgid', models.CharField(max_length=255)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField()),
            ],
            options={'ordering': ['date']},
        ),
        migrations.CreateModel(
            name='EmailConfirmation',
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
                (
                    'type',
                    models.CharField(
                        max_length=20,
                        choices=[
                            (b'userperson', b'User-Person association'),
                            (b'registration', b'Registration'),
                            (b'optout', b'Email opt-out'),
                        ],
                    ),
                ),
                ('email', models.CharField(max_length=200)),
                ('key', patchwork.models.HashField(max_length=40)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('active', models.BooleanField(default=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
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
                        max_length=200, serialize=False, primary_key=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Patch',
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
                ('msgid', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('archived', models.BooleanField(default=False)),
                ('headers', models.TextField(blank=True)),
                ('content', models.TextField(null=True, blank=True)),
                (
                    'pull_url',
                    models.CharField(max_length=255, null=True, blank=True),
                ),
                (
                    'commit_ref',
                    models.CharField(max_length=255, null=True, blank=True),
                ),
                (
                    'hash',
                    patchwork.models.HashField(
                        max_length=40, null=True, blank=True
                    ),
                ),
            ],
            options={'ordering': ['date'], 'verbose_name_plural': 'Patches'},
        ),
        migrations.CreateModel(
            name='PatchTag',
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
                ('count', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
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
                ('email', models.CharField(unique=True, max_length=255)),
                (
                    'name',
                    models.CharField(max_length=255, null=True, blank=True),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
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
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('linkname', models.CharField(unique=True, max_length=255)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('listid', models.CharField(unique=True, max_length=255)),
                ('listemail', models.CharField(max_length=200)),
                ('web_url', models.CharField(max_length=2000, blank=True)),
                ('scm_url', models.CharField(max_length=2000, blank=True)),
                ('webscm_url', models.CharField(max_length=2000, blank=True)),
                ('send_notifications', models.BooleanField(default=False)),
                ('use_tags', models.BooleanField(default=True)),
            ],
            options={'ordering': ['linkname']},
        ),
        migrations.CreateModel(
            name='State',
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
                ('name', models.CharField(max_length=100)),
                ('ordering', models.IntegerField(unique=True)),
                ('action_required', models.BooleanField(default=True)),
            ],
            options={'ordering': ['ordering']},
        ),
        migrations.CreateModel(
            name='Tag',
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
                ('name', models.CharField(max_length=20)),
                (
                    'pattern',
                    models.CharField(
                        help_text=b'A simple regex to match the tag in the '
                                  b'content of a message. Will be used with '
                                  b'MULTILINE and IGNORECASE flags. eg. '
                                  b'^Acked-by:',
                        max_length=50,
                    ),
                ),
                (
                    'abbrev',
                    models.CharField(
                        help_text=b'Short (one-or-two letter) abbreviation '
                                  b'for the tag, used in table column headers',
                        unique=True,
                        max_length=2,
                    ),
                ),
            ],
            options={'ordering': ['abbrev']},
        ),
        migrations.CreateModel(
            name='UserProfile',
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
                (
                    'send_email',
                    models.BooleanField(
                        default=False,
                        help_text=b'Selecting this option allows patchwork to '
                                  b'send email on your behalf',
                    ),
                ),
                (
                    'patches_per_page',
                    models.PositiveIntegerField(
                        default=100,
                        help_text=b'Number of patches to display per page',
                    ),
                ),
                (
                    'maintainer_projects',
                    models.ManyToManyField(
                        related_name='maintainer_project',
                        to='patchwork.Project',
                    ),
                ),
                (
                    'primary_project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        blank=True,
                        to='patchwork.Project',
                        null=True,
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
                    models.DateTimeField(default=datetime.datetime.now),
                ),
                (
                    'orig_state',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.State',
                    ),
                ),
            ],
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
            model_name='patchtag',
            name='tag',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='patchwork.Tag'
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='delegate',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='state',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.State',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='submitter',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Person',
            ),
        ),
        migrations.AddField(
            model_name='patch',
            name='tags',
            field=models.ManyToManyField(
                to='patchwork.Tag', through='patchwork.PatchTag'
            ),
        ),
        migrations.AddField(
            model_name='comment',
            name='patch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Patch',
            ),
        ),
        migrations.AddField(
            model_name='comment',
            name='submitter',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Person',
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
                to='patchwork.Patch', through='patchwork.BundlePatch'
            ),
        ),
        migrations.AddField(
            model_name='bundle',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='patchwork.Project',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='patchtag', unique_together=set([('patch', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='patch', unique_together=set([('msgid', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='comment', unique_together=set([('msgid', 'patch')]),
        ),
        migrations.AlterUniqueTogether(
            name='bundlepatch', unique_together=set([('bundle', 'patch')]),
        ),
        migrations.AlterUniqueTogether(
            name='bundle', unique_together=set([('owner', 'name')]),
        ),
    ]
