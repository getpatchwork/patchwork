Installation
============

This document describes the necessary steps to configure Patchwork in a
development environment. If you are interested in deploying Patchwork in a
production environment, refer to `the deployment guide
<../deployment/installation>`__ instead.

To begin, you should clone Patchwork:

.. code-block:: shell

   $ git clone git://github.com/getpatchwork/patchwork.git

Docker-Based Installation
-------------------------

Patchwork provides a Docker-based environment for quick configuration of a
development environment. This is the preferred installation method. To
configure Patchwork using Docker:

1. Install `docker`_ and `docker-compose`_.

2. Build the images. This will download over 200MB from the internet:

   .. code-block:: shell

      $ docker-compose build

3. Run `docker-compose up`:

   .. code-block:: shell

      $ docker-compose up

   This will be visible at http://localhost:8000/.

To run a shell within this environment, run:

.. code-block:: shell

   $ docker-compose run --rm web --shell

To run `django-manage` commands, such as `createsuperuser` or `migrate`, run:

.. code-block:: shell

   $ docker-compose run --rm web python manage.py createsuperuser

To access the SQL command-line client, run:

.. code-block:: shell

   $ docker-compose run --rm web python manage.py dbshell

To run unit tests, excluding Selenium UI interaction tests, using only the
package versions installed during container initialization, run:

.. code-block:: shell

   $ docker-compose run --rm web --quick-test

To run the same against all supported versions of Django (via tox), run:

.. code-block:: shell

   $ docker-compose run --rm web --quick-tox

To run specific tox targets or tests, pass arguments to the above:

.. code-block:: shell

   $ docker-compose run --rm web --quick-tox -e py27-django18 \
       patchwork.tests.test_bundles

To run all tests, including Selenium UI interaction tests, using only the
package versions installed container initialization, run:

.. code-block:: shell

   $ docker-compose run --rm web --test

To run the same against all supported versions of Django (via tox), run:

.. code-block:: shell

   $ docker-compose run --rm web --tox

To run all tests, including Selenium UI interaction tests in non-headless mode,
run:

.. code-block:: shell

   $ docker run -it --rm -v (pwd):/home/patchwork/patchwork/ \
       --link patchwork_db_1:db -p 8000:8000 \
       -v /tmp/.X11-unix:/tmp/.X11-unix \
       -e PW_TEST_DB_HOST=db -e DISPLAY patchwork_web bash

To reset the database before any of these commands, add ``--reset`` to the
command line after ``web`` and before any other arguments. Conversely, to
backup the database at any stage, run:

.. code-block:: shell

    $ docker exec DATABASECONTAINER /usr/bin/mysqldump -u DATABASEUSER \
        --password=DATABASEPASSWORD DATABASE > backup.sql

where ``DATABASECONTAINER`` is found by ``docker ps -a`` and the other settings
are the same as those defined in ``patchwork/settings/dev.py``. To restore this
again, run:

.. code-block:: shell

    $ docker-compose run --rm web python manage.py dbshell
    mysql> use DATABASE;
    mysql> set autocommit=0; source backup.sql; commit;
    mysql> exit;

Any local edits to the project files made locally are immediately visible to
the Docker container, and so should be picked up by the Django auto-reloader.

For more information on Docker itself, please refer to the `docker`_ and
`docker-compose`_ documentation.

.. note::

   If using SELinux, you will need to create a custom SELinux rule to allow the
   Docker process to access your working directory. Run:

   .. code-block:: shell

      $ chcon -RT svirt_sandbox_file_t $PATCHWORK_DIR

   where `$PATCHWORK_DIR` is the absolute patch to the `patchwork` folder
   created when you cloned the repo. For more information, see `man docker
   run`.

.. note::

   If you see an error like the below::

     ERROR: Couldn't connect to the Docker daemon at http+docker://localunixsocket - is it running?

   ensure you have correctly installed Docker, added your user to the `docker`
   group, and started the daemon, per the `docker documentation <docker>`_.

.. note::

   If you see an error like the below::

     py.error.EACCES: [Permission denied]: open('/home/patchwork/patchwork/.tox/py27-django18/.tox-config1', 'w')

   your host user account is likely using a different UID to the one hardcoded
   in the Dockerfile.  You can confirm this like so:

   .. code-block:: shell

      $ echo $UID
      1234

   If this is anything other than `1000`, you must must modify the `Dockerfile`
   found in `tools/docker` to use your UID and then rebuild:

   .. code-block:: shell

      $ sed -i "/ARG UID=/c\ARG UID=$(echo $UID)" tools/docker/Dockerfile
      $ docker-compose build web

   This change must be retained in the event that you rebuild the container.
   You can "hide" the change from Git like so:

   .. code-block:: shell

      $ git update-index --assume-unchanged tools/docker/Dockerfile
      $ git update-index --skip-worktree tools/docker/Dockerfile

   This should be resolved in a future release when we support docker-compose
   2.1 syntax in `docker-compose.yml`.

.. _docker: https://docs.docker.com/compose/install/
.. _docker-compose: https://docs.docker.com/engine/installation/linux/

Manual Installation
-------------------

Manual installation can be used where use of Docker is not possible
or desired.

Install Required Packages
~~~~~~~~~~~~~~~~~~~~~~~~~

There are a number of different requirements for developing Patchwork:

* Python and libraries

* A supported database (RDBMS)

These are detailed below.

Python Requirements
^^^^^^^^^^^^^^^^^^^

To develop Python-based software you first need Python. Patchwork supports both
Python 2.7 and Python 3.3+. One of these will be installed by default on many
installations, though they can also be installed manually using the `python` or
`python3` packages.

It's a good idea to use `virtual environments`__ to develop Python software.
Virtual environments are "instances" of your system Python without any of the
additional Python packages installed. They are useful to develop and possibly
deploy Patchwork against a "well known" set of dependencies, but they can also
be used to test Patchwork against several versions of Django.

If you do not have `virtualenv` installed then you should install it now. This
can be installed using the `python-virtualenv` or `python3-virtualenv`
packages. Alternatively you can install these using `pip`.

It is also helpful to install `tox` which is used for running tests in
Patchwork. This can be installed using the `python-tox` or `python3-tox`
packages, or via `pip`.

__ https://virtualenv.readthedocs.io/en/latest/

Database Requirements
^^^^^^^^^^^^^^^^^^^^^

If not already installed, you may need to install an RDBMS. You can use either
MariaDB/MySQL or PostgreSQL for this purpose. You should also install the
development headers, known as `libmysqlclient-dev` or `libpq-dev` respectively
on Debian-based Debian-based distros like Ubuntu and `mysql-devel` or
`postgresql-devel` on RHEL-based distros.

.. note::

   While Django provides support for `multiple database backends`__, Patchwork
   itself is only tested against MySQL/MariaDB and PostgreSQL. Should you wish
   to use a different backend, ensure you validate this first (and perhaps
   upstream any changes you may find necessary).

.. note::

   You may be tempted to use SQLite to develop Patchwork. We'd advise against
   doing this. SQLite supports a subset of the functionality of "full" RDBMS
   like MySQL: for example, case-sensitive matching of Unicode `is not
   supported`__. You will find some tests provided by Patchwork fail and some
   patches you develop may fail in production due to these differences.

__ https://docs.djangoproject.com/en/1.8/ref/databases/
__ https://www.sqlite.org/faq.html#q18

Example Installation
^^^^^^^^^^^^^^^^^^^^

An example for installing all these packages and the MySQL RDBMS on Ubuntu
15.04 is given below:

.. code-block:: shell

   $ sudo apt-get install python python-pip python-dev python-virtualenv \
       python-tox mysql-server libmysqlclient-dev

If you have an existing MariaDB/MySQL installation and have installed `pip`
already/are using Python 3.4+ then you can install all packages using `pip`:

.. code-block:: shell

   $ sudo pip install virtualenv tox

If you wish to use Python 3 then simply replace `python` with `python3` in the
above command.

Configure Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   If you are interested in simply :ref:`testing Patchwork <testing>`, many of
   the below steps are not required. tox will automatically install
   dependencies and use virtual environments when testing.

Once these requirements are installed, you should create and activate a new
virtual environment. This can be done like so:

.. code-block:: shell

   $ virtualenv .venv
   $ source .venv/bin/activate
   (.venv)$

.. note::

   If you installed a Python 3.x-based virtual environment package, adjust the
   executable indicated above as necessary, e.g. `virtualenv-3.4`.

Now install the packages. Patchwork provides three requirements files.

`requirements-dev.txt`

  Packages required to configure a development environment

`requirements-prod.txt`

  Packages required for deploying Patchwork in production

`requirements-test.txt`

  Packages required to run tests

We're going to install the first of these, which can be done like so:

.. code-block:: shell

   (.venv)$ cd patchwork
   (.venv)$ pip install -r requirements-dev.txt

.. note::

   Once configured this does not need to be done again *unless* the
   requirements change, e.g. Patchwork requires an updated version of Django.

Initialize the Database
~~~~~~~~~~~~~~~~~~~~~~~

One installed, the database must be configured. We will assume you have root
access to the database for these steps.

To begin, export your database credentials as follows:

.. code-block:: shell

   (.venv)$ db_user=root
   (.venv)$ db_pass=password

Now, create the database. If this is your first time configuring the database,
you must create a `patchwork` user (or similar) along with the database
instance itself. The commands below will do this, dropping existing databases
if necessary:

.. code-block:: shell

   (.venv)$ mysql -u$db_user -p$db_pass << EOF
   DROP DATABASE IF EXISTS patchwork;
   CREATE DATABASE patchwork CHARACTER SET utf8;
   GRANT ALL PRIVILEGES ON patchwork.* TO 'patchwork'@'localhost'
       IDENTIFIED BY 'password';
   EOF

.. note::

   The `patchwork` username and `password` password are the defaults expected
   by the provided `dev` settings files. If using something different,
   export the `PW_TEST_DB_USER` and `PW_TEST_DB_PASS` variables described in
   the :ref:`Environment Variables <dev-envvar>` section below.  Alternatively,
   you can create your own settings file with these variables hardcoded and
   change the value of `DJANGO_SETTINGS_MODULE` as described below.

Load Initial Data
~~~~~~~~~~~~~~~~~

Before continuing, we need to tell Django where it can find our configuration.
Patchwork provides a default development `settings.py` file for this purpose.
To use this, export the `DJANGO_SETTINGS_MODULE` environment variable as
described below:

.. code-block:: shell

   (.venv)$ export DJANGO_SETTINGS_MODULE=patchwork.settings.dev

Alternatively you can provide your own `settings.py` file and provide the path
to that instead.

Once done, we need to create the tables in the database. This can be done using
the `migrate` command of the `manage.py` executable:

.. code-block:: shell

   (.venv)$ ./manage.py migrate

Next, you should load the initial fixtures into Patchwork. These initial
fixtures provide.

`default_tags.xml`

  The tags that Patchwork will extract from mails. For example: `Acked-By`,
  `Reviewed-By`

`default_states.xml`

  The states that a patch can be in. For example: `Accepted`, `Rejected`

`default_projects.xml`

  A default project that you can then upload patches for

These can be loaded using the `loaddata` command:

.. code-block:: shell

   (.venv)$ ./manage.py loaddata default_tags default_states default_projects

You should also take the opportunity to create a "superuser". You can do this
using the aptly-named `createsuperuser` command:

.. code-block:: shell

   (.venv)$ ./manage.py createsuperuser

Import Mailing List Archives
----------------------------

Regardless of your installation method of choice, you will probably want to
load some real emails into the system.  This can be done manually, however it's
generally much easier to download an archive from a Mailman instance and load
these using the `parsearchive` command. You can do this like so:

.. code-block:: shell

   (.venv)$ mm_user=<myusername>
   (.venv)$ mm_pass=<mypassword>
   (.venv)$ mm_host=https://lists.ozlabs.org
   (.venv)$ mm_url=$mm_host/private/patchwork.mbox/patchwork.mbox
   (.venv)$ curl -F username=$mm_user -F password=$mm_pass -k -O $mm_url

where `mm_user` and `mm_pass` are the username and password you have registered
with on the Mailman instance found at `mm_host`.

.. note::

   We provide instructions for downloading archives from the Patchwork mailing
   list, but almost any instance of Mailman will allow downloading of archives
   as seen above; simply change the `pw_url` variable defined. You can find
   more informations about this `here`__.

Load these archives into Patchwork. Depending on the size of the downloaded
archives this may take some time:

.. code-block:: shell

   (.venv)$ ./manage.py parsearchive --list-id=patchwork.ozlabs.org \
      patchwork.mbox

Finally, run the server and browse to the IP address of your board using your
browser of choice:

.. code-block:: shell

   (.venv)$ ./manage.py runserver 0.0.0.0:8000

Once finished, you can kill the server (`Ctrl` + `C`) and exit the virtual
environment:

.. code-block:: shell

   (.venv)$ deactivate
   $

Should you wish to re-enter this environment, simply source the `activate`
script again.

__ http://blog.behnel.de/posts/indexp118.html

Django Debug Toolbar
--------------------

Patchwork installs and enables the 'Django Debug Toolbar' by default. However,
by default this is only displayed if you are developing on localhost. If
developing on a different machine, you should configure an SSH tunnel such
that, for example, `localhost:8000` points to `[DEV_MACHINE_IP]:8000`.

.. _dev-envvar:

Environment Variables
---------------------

The following environment variables are available to configure settings when
using the provided `dev` settings file.

`PW_TEST_DB_NAME=patchwork`

  Name of the database

`PW_TEST_DB_USER=patchwork`

  Username to access the database with

`PW_TEST_DB_PASS=password`

  Password to access the database with<

`PW_TEST_DB_TYPE=mysql`

  Type of database to use. Options: 'mysql', 'postgres'
