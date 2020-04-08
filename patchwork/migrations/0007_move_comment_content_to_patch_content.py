from django.db import connection, migrations


def copy_comment_field(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute(
            '''
            UPDATE patchwork_patch
              SET content = patchwork_comment.content
            FROM patchwork_comment
              WHERE patchwork_patch.id=patchwork_comment.patch_id
                    AND patchwork_patch.msgid=patchwork_comment.msgid
        '''
        )
    elif connection.vendor == 'mysql':
        schema_editor.execute(
            '''
            UPDATE patchwork_patch, patchwork_comment
              SET patchwork_patch.content = patchwork_comment.content
            WHERE patchwork_patch.id=patchwork_comment.patch_id
              AND patchwork_patch.msgid=patchwork_comment.msgid
        '''
        )
    else:
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


def remove_duplicate_comments(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute(
            '''
            DELETE FROM patchwork_comment
              USING patchwork_patch
              WHERE patchwork_patch.id=patchwork_comment.patch_id
                    AND patchwork_patch.msgid=patchwork_comment.msgid
        '''
        )
    elif connection.vendor == 'mysql':
        schema_editor.execute(
            '''
            DELETE FROM patchwork_comment
              USING patchwork_patch, patchwork_comment
              WHERE patchwork_patch.id=patchwork_comment.patch_id
                    AND patchwork_patch.msgid=patchwork_comment.msgid
        '''
        )
    else:
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


def uncopy_comment_field(apps, schema_editor):
    # This is no-op because the column is being deleted
    pass


def recreate_comments(apps, schema_editor):
    Comment = apps.get_model('patchwork', 'Comment')
    Patch = apps.get_model('patchwork', 'Patch')

    for patch in Patch.objects.all():
        if patch.content:
            comment = Comment(
                patch=patch,
                msgid=patch.msgid,
                date=patch.date,
                headers=patch.headers,
                submitter=patch.submitter,
                content=patch.content,
            )
            comment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0006_add_patch_diff'),
    ]

    operations = [
        migrations.RunPython(
            copy_comment_field, uncopy_comment_field, atomic=False
        ),
        migrations.RunPython(
            remove_duplicate_comments, recreate_comments, atomic=False
        ),
    ]
