v1.0 Series ("Burlap")
======================

1.0.0
-----

This release changes a few admin-visible components of Patchwork, so upgrading
involves a few steps.

New Features
~~~~~~~~~~~~

- Patch tags are now supported

  Patch "tags", such as `Acked-by`, `Reviewed-by`, are typically included in
  patches and replies. They provide important information as to the activity
  and "mergability" of a patch. These tags are now extracted from patches and
  included in the patch list.

- Django 1.7 and Django 1.8 are now supported

- tox support is integrated for use by developers

Upgrade Notes
~~~~~~~~~~~~~

- Migrations are now executed using the Django migrations framework.

  Future database migrations will be implemented using Django Migrations,
  rather than raw SQL scripts. Before switching to Django migrations, first
  apply any unapplied migrations in the `lib/sql/migration` folder. For
  example, on postgres::

    $ psql -f lib/sql/migration/015-add-patch-tags.sql patchwork
    $ psql -f lib/sql/grant-all.postgres.sql patchwork

  Once applied, configure the required Django Migration tables using the
  `migrate` managment command::

    $ ./manage.py migrate --fake-initial

- Moved Patchwork source from the `apps` directory to the top level directory.

  Any scripts or tools that call Patchwork applications, such as
  `parsemail.sh`, must be updated to reference the new location of these
  scripts. To do this, simply remove `apps/` from the path, i.e.
  `apps/patchwork/` becomes `patchwork`.

- The `patchwork-cron.py` script has been replaced by the `cron` management
  command.

  Any references to the former should be updated to the latter. The `cron`
  management command can be called like so::

    $ ./manage.py cron

- The `settings.py` file has been updated to reflect modern Django practices.

  You may need to manually migrate your existing configuration to the new
  settings file(s). By default, settings are read from
  `patchwork/settings/production.py`. To migrate, use the provided template::

    $ cp patchwork/settings/production{.example,}.py

  Merge your previous settings, usually located in `apps/local_settings.py`, to
  this file.

  In addition, any scripts that set the `DJANGO_SETTINGS_MODULE` environment
  variable will need to be updated to reflect the new location, typically::

    DJANGO_SETTINGS_MODULE=patchwork.settings.production

- Django `staticfiles` is now used to to gather static files for for serving
  via a web server

  Static content should now be located in the folder indicated by
  `STATIC_ROOT`.  This should point to somewhere sensible, such as the absolute
  path of `htdocs/static` in the Patchwork tree. Configure the `STATIC_ROOT`
  setting in your settings file, then run the `collectstatic` management
  command::

    $ ./manage.py collectstatic

  Finally, update your webserver configuration to serve the static content from
  this new location. Refer to the sample web configuration files provided in
  `lib` for more information.

- Django 1.5 is no longer supported

- Python 2.5 support was broken and is officially no longer supported

Deprecation Notes
~~~~~~~~~~~~~~~~~

- Django 1.6 support will be removed in a future release

- Raw SQL migration scripts, currently found at `lib/sql/migration`, will no
  longer be updated and will be removed in a future release. The Django
  Migration framework, found in Django 1.7 and above, should be used instead.
