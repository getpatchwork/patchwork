import patchwork.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('patchwork', '0046_patch_comment_events'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patch',
            name='hash',
            field=patchwork.fields.HashField(
                blank=True, db_index=True, max_length=40, null=True
            ),
        ),
    ]
