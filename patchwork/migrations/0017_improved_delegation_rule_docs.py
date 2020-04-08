from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0016_series_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delegationrule',
            name='path',
            field=models.CharField(
                help_text=b'An fnmatch-style pattern to match filenames '
                          b'against.',
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name='delegationrule',
            name='priority',
            field=models.IntegerField(
                default=0,
                help_text=b'The priority of the rule. Rules with a higher '
                          b'priority will override rules with lower '
                          b'priorities',
            ),
        ),
        migrations.AlterField(
            model_name='delegationrule',
            name='user',
            field=models.ForeignKey(
                help_text=b'A user to delegate the patch to.',
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
