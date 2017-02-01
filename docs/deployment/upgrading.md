# Upgrading

**NOTE:** This document provides some general tips and tricks that one can use
when upgrading an existing, production installation of Patchwork. If you are
interested in the specific changes between each release, please refer to the
[`UPGRADING` document][gh-upgrading] instead. If this is your first time
installing Patchwork, please refer to the
[installation guide][doc-installation] instead.

## Before You Start

Before doing anything, always **backup your data**. This generally means
backing up your database, but it might also be a good idea to backup your
environment in case you encounter issues during the upgrade process.

While Patchwork won't explicitly prevent it, it's generally wise to avoid
upgrades spanning multiple releases in one go. An iterative upgrade approach
will provide an easier, if slower, upgrade process.

## Identify Changed Scripts, Requirements, etc.

The `UPGRADING` document provides a comprehensive listing of all
backwards-incompatible changes that occur between releases of Patchwork.
Examples of such changes include:

* Moved/removed scripts and files
* Changes to the requirements, e.g. supported Django versions
* Changes to API that may affect, for example, third-party tools

It is important that you understand these changes and ensure any scripts you
may have, such as systemd/upstart scripts, are modified accordingly.

## Understand What Requirements Have Changed

New versions of Patchwork can often require additional or updated version of
dependencies, e.g. newer versions of Django. It is important that you
understand these requirements and can fulfil them. This is particularly true
for users relying on distro-provided packages, who may have to deal with older
versions of a package or may be missing a package altogether (though we try to
avoid this). Such changes are usually listed in the `UPGRADING` document, but
you can also diff the `requirements.txt` files in each release for comparison.

## Collect Static Files

New versions of Patchwork generally contain changes to the additional files
like images, CSS and JavaScript. To do this, run the `collectstatic`
management commands:

    $ ./manage.py collectstatic

## Upgrade Your Database

Migrations of the database can be tricky. Prior to [`v1.0.0`][gh-v1], database
migrations were provided by way of manual, SQL migration scripts. After this
release, Patchwork moved to support [Django migrations][ref-django-migrate].
If you are upgrading from `v1.0.0` or later, it is likely that you can rely
entirely on the later to bring your database up-to-date. This can be done like
so:

    $ ./manage.py migrate

However, there are a number of scenarios in which you may need to fall back to
the provided SQL migrations or provide your own:

* You are using Django < 1.6

  Patchwork supports Django 1.6. However, Django Migrations was added in 1.7
  and is [not available for previous versions][ref-south2]. As such, you must
  continue to use manual migrations or upgrade your version of Django. For
  many of the migrations, this can be done automatically:

      $ ./manage.py sqlmigrate patchwork 0003_add_check_model

  However, this only works for schema migrations. For data migrations,
  however, this will fail. In this cases, these migrations will need to be
  handwritten.

* You are using Django > 1.6, but upgrading from Patchwork < 1.0.0

  Patchwork only started providing migrations in `v1.0.0`. SQL migrations are
  provided for versions prior to this and must be applied to get the database
  to the "initial" state that Django migrations expects.

* You have diverged from upstream Patchwork

  If you have applied custom patches that change the database models, the
  database in an "inconsistent state" and the provided migrations will likely
  fail to apply.

Steps to handle the latter two of these are described below.

### Upgrading a pre-v1.0.0 Patchwork instance

The process for this type of upgrade is quite simple: upgrade using manual
SQL upgrades until better options become available. As such, you should apply
all unapplied SQL migrations that are not duplicated by Django migrations.
Once such duplication occurs, rely on the Django migrations only and continue
to do so going forward.

### Upgrading a "diverged" Patchwork instance

This type of upgrade is a little trickier. There are two options you can take:

1. Bring your Patchwork instance back in sync with upstream
2. Provide your own migrations

The former option is particularly suitable if you decide to upstream your
change or decide it's not valuable enough to retain. This will require either
reworking any migrations that exist prior to your feature being upstreamed, or
deleting any added database fields and tables, respectively. In both cases,
manually, hand-written SQL migrations will be required to get the databse into
a consistent state (remember: **backup**!). Once this is done, you can resume
using the upstream-provided migrations, ensuring any Django migrations that you
may have skipped are not applied again:

    $ ./manage.py migrate 000x-abc --fake  # when 000x-abc is last "skippable"

It's worth adding that with the databases now back in sync it should be
possible to return to using upstream code rather than maintaining a fork.

The latter option is best chosen if you wish to retain the aforementioned fork.
How you do this depends on the extensiveness of your changes, but getting the
latest version of Patchwork, deleting the provided migrations, applying any
patches you may have and regenerating the migrations seems like the best
option.

**NOTE**: To prevent the latter case above from occurring, we'd ask that you
submit any patches you may have to the upstream Patchwork so that the wider
community can benefit from this new functionality. Please see
[the contributing document][doc-contributing] for more information on this
process.

[doc-installation]: installation.md
[doc-contributing]: ../development/contributing.md
[gh-upgrading]: https://github.com/getpatchwork/patchwork/blob/master/UPGRADING.md
[gh-v1]: https://github.com/getpatchwork/patchwork/releases/tag/v1.0.0
[ref-django-migrate]: https://docs.djangoproject.com/en/1.8/topics/migrations/
[ref-south2]: http://blog.allenap.me/2015/05/south-south-2-and-django-migrations.html
