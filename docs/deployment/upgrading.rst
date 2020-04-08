Upgrading
=========

This document provides some general tips and tricks that one can use when
upgrading an existing, production installation of Patchwork. If you are
interested in the specific changes between each release, refer to
:doc:`/releases/index` instead. If this is your first time installing
Patchwork, refer to the :doc:`installation` instead.

Before You Start
----------------

Before doing anything, always **backup your data**. This generally means
backing up your database, but it might also be a good idea to backup your
environment in case you encounter issues during the upgrade process.

While Patchwork won't explicitly prevent it, it's generally wise to avoid
upgrades spanning multiple releases in one go. An iterative upgrade approach
will provide an easier, if slower, upgrade process.

Identify Changed Scripts, Requirements, etc.
--------------------------------------------

:doc:`/releases/index` provides a comprehensive listing of all
backwards-incompatible changes that occur between releases of Patchwork.
Examples of such changes include:

* Moved/removed scripts and files

* Changes to the requirements, e.g. supported Django versions

* Changes to API that may affect, for example, third-party tools

It is important that you understand these changes and ensure any scripts you
may have, such as systemd scripts, are modified accordingly.

Understand What Requirements Have Changed
-----------------------------------------

New versions of Patchwork can often require additional or updated version of
dependencies, e.g. newer versions of Django. It is important that you
understand these requirements and can fulfil them. This is particularly true
for users relying on distro-provided packages, who may have to deal with older
versions of a package or may be missing a package altogether (though we try to
avoid this). Such changes are usually listed in the :doc:`/releases/index`, but
you can also diff the `requirements.txt` files in each release for comparison.

Collect Static Files
--------------------

New versions of Patchwork generally contain changes to the additional files
like images, CSS and JavaScript. To do this, run the `collectstatic`
management commands:

.. code-block:: shell

   $ ./manage.py collectstatic

Upgrade Your Database
---------------------

New versions of Patchwork may provide a number of schema and/or data migrations
which must be applied before starting the instance. To do this, run the
*migrate* management command:

.. code-block:: shell

   $ ./manage.py migrate

For more information on migrations, refer to `the Django documentation`__.

__ https://docs.djangoproject.com/en/2.2/topics/migrations/
