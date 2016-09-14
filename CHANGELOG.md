# Change Log

All notable changes to this project will be documented in this file. Please
refer to the release notes for more detailed information, e.g. how to upgrade.

This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

- N/A

## [1.1.0] - 2016-03-03

This release overhauled the web UI and added support for automatic delegation
of patches, test result capture, and Python 3.4.

### Added

- Python 3.4 support
- Check feature, which can be used to report the status of tests
- Automatic delegation of patches based on file path
- Automated documentation for the XML-RPC API. This can be found at the
  '/xmlrpc' in most Patchwork deployments
- Vagrant support for developers
- Selenium-based UI tests for developers

### Changed

- Overhauled the web UI to reflect modern web standards
- Patches can now be delegated to any Patchwork user
- Significant updates to the documentation
- Assorted cleanup tasks and bug fixes

## [1.0.0] - 2015-10-26

### Added

- Patch tag infrastructure feature, which provides a quick summary of patch
  "tags" (e.g. `Acked-by`, `Reviewed-by`, ...) found in a patch and its replies
- Django 1.7 and Django 1.8 support
- Django `staticfiles` support, which should be used to gather static files for
  for serving via a web server
- tox support for developers

### Changed

- Migrations are now executed using the Django migrations framework
- Moved Patchwork source from the `apps` directory to the top level directory
- The `cron` Django management command has replaced the `bin/patchwork-cron`
  script
- Rewrote documentation to reflect changes in development and deployment best
  practices over the past few years
- Reworked `requirements.txt` and `settings.py` files

### Removed

- Django 1.5 support
- Defunct Python 2.5 code
- Numerous dead files/code

### Deprecated

- Django 1.6 support will be removed in a future release
- Raw SQL migration scripts, previously found at `lib/sql/migration`, will no
  longer be provided. Use the Django Migration framework found in Django 1.7
  and above

### Additional notes

This version changes a few admin-visible components of Patchwork, so upgrading
involves a few steps.

#### Update settings

By default, settings are read from `patchwork/settings/production.py`. To
migrate, use the provided template:

    $ cp patchwork/settings/production{.example,}.py

Merge your previous settings, usually located in `apps/local_settings.py`, to
this file.

#### Fix external references

Any scripts or tools that call Patchwork applications, such as `parsemail.sh`,
must be updated to reference the new location of these scripts. To do this,
simply remove `apps/` from the path, i.e. `apps/patchwork/` becomes
`patchwork`.

In addition, any scripts that set the `DJANGO_SETTINGS_MODULE` environment
variable will need to be updated to reflect the new location, typically:

    DJANGO_SETTINGS_MODULE=patchwork.settings.production

Finally, as the `patchwork-cron.py` script has been replaced by the `cron`
management command, any references to the former should be updated to the
latter. The `cron` management command can be called like so:

    $ ./manage.py cron

#### Migrate to Django Migrations

Future database migrations will be implemented using Django Migrations, rather
than raw SQL scripts. Before switching to Django migrations, first apply any
unapplied migrations in the `lib/sql/migration` folder. For example, on
postgres:

    $ psql -f lib/sql/migration/015-add-patch-tags.sql patchwork
    $ psql -f lib/sql/grant-all.postgres.sql patchwork

Once applied, configure the required Django Migration tables using the
`migrate` managment command:

    $ ./manage.py migrate --fake-initial

#### Migrate to Django Staticfiles

Static content should now be located in the folder indicated by `STATIC_ROOT`.
This should point to somewhere sensible, such as the absolute path of
`htdocs/static` in the Patchwork tree. Configure the `STATIC_ROOT` setting in
your settings file, then run the `collectstatic` management command:

    $ ./manage.py collectstatic

Finally, update your webserver's configuration to serve the static content from
this new location. Refer to the sample web configuration files provided in
`lib` for more information.

## [0.9.0] - 2015-03-22

**NOTE:** 1.0.0 was the first release of Patchwork adopting semantic versioning.
For information on *"0.9.0"* and before, please refer to Git logs.

[Unreleased]: https://github.com/getpatchwork/patchwork/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/getpatchwork/patchwork/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/getpatchwork/patchwork/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/getpatchwork/patchwork/compare/c561ebe...v0.9.0

