from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0025_add_regex_validators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bundle',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='bundles',
                related_query_name='bundle',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
