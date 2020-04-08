from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0004_add_delegation_rule_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='maintainer_projects',
            field=models.ManyToManyField(
                related_name='maintainer_project',
                to='patchwork.Project',
                blank=True,
            ),
        ),
    ]
