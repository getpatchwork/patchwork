from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0009_add_submission_model'),
    ]

    operations = [
        migrations.RunSQL(
            '''INSERT INTO patchwork_patch
                  (submission_ptr_id, diff2, commit_ref2, pull_url2,
                   delegate2_id, state2_id, archived2, hash2)
                SELECT id, diff, commit_ref, pull_url, delegate_id, state_id,
                       archived, hash
                FROM patchwork_submission
                ''',
            '''UPDATE patchwork_submission SET
                  diff=diff2, commit_ref=commit_ref2, pull_url=pull_url2,
                  delegate_id=delegate2_id, state_id=state2_id,
                  archived=archived2, hash=hash2
                FROM patchwork_patch WHERE
                  patchwork_submission.id = patchwork_patch.submission_ptr_id
                ''',
        ),
    ]
