# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_comment_field(apps, schema_editor):
    Comment = apps.get_model('patchwork', 'Comment')
    Patch = apps.get_model('patchwork', 'Patch')

    for patch in Patch.objects.all():
        try:
            # when available, this can only return one entry due to the
            # unique_together constraint
            comment = Comment.objects.get(patch=patch, msgid=patch.msgid)
        except Comment.DoesNotExist:
            # though there's no requirement to actually have a comment
            continue

        patch.content = comment.content
        patch.save()


def uncopy_comment_field(apps, schema_editor):
    Patch = apps.get_model('patchwork', 'Patch')

    for patch in Patch.objects.all():
        patch.content = None
        patch.save()


def remove_duplicate_comments(apps, schema_editor):
    Comment = apps.get_model('patchwork', 'Comment')
    Patch = apps.get_model('patchwork', 'Patch')

    for patch in Patch.objects.all():
        try:
            # when available, this can only return one entry due to the
            # unique_together constraint
            comment = Comment.objects.get(patch=patch, msgid=patch.msgid)
            comment.delete()
        except Comment.DoesNotExist:
            # though there's no requirement to actually have a comment
            continue


def recreate_comments(apps, schema_editor):
    Comment = apps.get_model('patchwork', 'Comment')
    Patch = apps.get_model('patchwork', 'Patch')

    for patch in Patch.objects.all():
        if patch.content:
            comment = Comment(patch=patch, msgid=patch.msgid, date=patch.date,
                              headers=patch.headers, submitter=patch.submitter,
                              content=patch.content)
            comment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0006_add_patch_diff'),
    ]

    operations = [
        migrations.RunPython(copy_comment_field, uncopy_comment_field),
        migrations.RunPython(remove_duplicate_comments, recreate_comments),
    ]
