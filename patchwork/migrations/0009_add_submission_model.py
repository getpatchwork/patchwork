from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import patchwork.models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0008_add_email_mixin'),
    ]

    operations = [
        # Rename the 'Patch' to 'Submission'
        migrations.RenameModel(old_name='Patch', new_name='Submission'),
        migrations.AlterModelOptions(
            name='submission', options={'ordering': ['date']},
        ),
        # Rename the non-Patch specific references to point to Submission
        migrations.RenameField(
            model_name='comment', old_name='patch', new_name='submission',
        ),
        migrations.AlterUniqueTogether(
            name='comment', unique_together=set([('msgid', 'submission')]),
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='patches_per_page',
            new_name='items_per_page',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='items_per_page',
            field=models.PositiveIntegerField(
                default=100, help_text=b'Number of items to display per page'
            ),
        ),
        # Recreate the 'Patch' model as a subclass of 'Submission'. Each field
        # is given a unique name to prevent it conflicting with the same field
        # found in the 'Submission' "super model". We will fix this later.
        migrations.CreateModel(
            name='Patch',
            fields=[
                (
                    'submission_ptr',
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        serialize=False,
                        to='patchwork.Submission',
                    ),
                ),
                ('diff2', models.TextField(null=True, blank=True)),
                (
                    'commit_ref2',
                    models.CharField(max_length=255, null=True, blank=True),
                ),
                (
                    'pull_url2',
                    models.CharField(max_length=255, null=True, blank=True),
                ),
                # we won't migrate the data of this, seeing as it's
                # automatically recreated every time we save a Patch
                (
                    'tags2',
                    models.ManyToManyField(
                        to='patchwork.Tag', through='patchwork.PatchTag'
                    ),
                ),
                (
                    'delegate2',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                    ),
                ),
                (
                    'state2',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='patchwork.State',
                    ),
                ),
                ('archived2', models.BooleanField(default=False)),
                (
                    'hash2',
                    patchwork.models.HashField(
                        max_length=40, null=True, blank=True
                    ),
                ),
            ],
            options={'verbose_name_plural': 'Patches'},
            bases=('patchwork.submission',),
        ),
    ]
