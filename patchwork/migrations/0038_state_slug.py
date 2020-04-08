from django.db import migrations, models, transaction
from django.utils.text import slugify


def validate_uniqueness(apps, schema_editor):
    """Ensure all State.name entries are unique.

    We need to do this before enforcing a uniqueness constraint.
    """

    State = apps.get_model('patchwork', 'State')

    total_count = State.objects.count()
    slugs_count = len(
        set([slugify(state.name) for state in State.objects.all()])
    )

    if slugs_count != total_count:
        raise Exception(
            'You have non-unique States entries that need to be combined '
            'before you can run this migration. This migration must be done '
            'by hand. If you need assistance, please contact '
            'patchwork@ozlabs.org'
        )


def populate_slug_field(apps, schema_editor):

    State = apps.get_model('patchwork', 'State')

    with transaction.atomic():
        for state in State.objects.all():
            state.slug = slugify(state.name)
            state.save()


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0037_event_actor'),
    ]

    operations = [
        # Ensure all 'State.name' entries are unique
        migrations.RunPython(validate_uniqueness, migrations.RunPython.noop),
        # Apply the unique constraint to 'State.name'
        migrations.AlterField(
            model_name='state',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        # Add a 'State.slug' field but allow it to be nullable
        migrations.AddField(
            model_name='state',
            name='slug',
            field=models.SlugField(
                blank=True, max_length=100, null=True, unique=True
            ),
        ),
        # Populate the 'State.slug' field
        migrations.RunPython(populate_slug_field, migrations.RunPython.noop),
        # Make the 'State.slug' field non-nullable
        migrations.AlterField(
            model_name='state',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
    ]
