# Patchwork Upgrade Guide

## 0.9.0 to 1.0.0

Version 1.0.0 changes a few admin-visible components of patchwork so
upgrading involves a few steps.

### Database Migrations

Update the database schema, by running the `015-add-patch-tags.sql` script,
and re-run the grants script. For example, on postgres:

    psql -f lib/sql/migration/015-add-patch-tags.sql patchwork
    psql -f lib/sql/grant-all.postgres.sql patchwork

### Update to the new settings infrastructure

By default, settings are read from `patchwork/settings/production.py`. To
migrate, use the template:

    cp patchwork/settings/production{.example,}.py

Merge your previous settings (from `apps/local_settings.py`) into this file.

### Fixup external references to `apps/`

The `apps/` directory is gone; the patchwork module is now in the top-level
directory. If you have scripts that run anything from `apps/` (e.g. incoming
mail parsers that call `parsemail.sh`, and cron scripts), then remove the
`apps/` directory from those:

    apps/patchwork/ -> patchwork/

Alternatively, you can create a symlink - `apps/ -> .`

If you have been running scripts (eg, from cron) that set the
`DJANGO_SETTINGS_MODULE` environment variable, you'll need to update that to
the new settings system. Typically:

    DJANGO_SETTINGS_MODULE=patchwork.settings.production

The `manage.py` script has been moved from apps/ into the top-level directory
too.

### Migrate to the `staticfiles` module

Static content should now be located in the folder indicated by `STATIC_ROOT`.
This should point somewhere sensible (e.g. the absolute path of `htdocs/static`
in the patchwork tree).

You'll need to set the `STATIC_ROOT` setting in your settings file.

Once settings are configured, run the 'collectstatic' management command:

    ./manage.py collectstatic

You also need to update your Apache configuration to use the new static
content. Since static content is now in all under `STATIC_ROOT`, the
configuration should be simpler than in previous releases. The core config
will be:

    DocumentRoot /srv/patchwork/htdocs/
    Alias /static/ /srv/patchwork/htdocs/static/
    WSGIScriptAlias / /srv/pathchwork/lib/apache2/patchwork.wsgi
    WSGIPassAuthorization On

### Use new management console

The patchwork cron script (`bin/patchwork-cron.py`) has been moved to a
`manage.py` command. Instead of running `patchwork-cron.py`, you should now
run:

    ./manage.py cron

