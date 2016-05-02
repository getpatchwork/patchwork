# Development

This document describes the necessary steps to configure Patchwork in a
development environment. If you are interested in deploying Patchwork in a
production environment, please refer to [the deployment guide][doc-deployment]
instead.

## Download Patchwork

The latest version of Patchwork is available with git. To download:

    $ git clone git://github.com/getpatchwork/patchwork.git

## Vagrant-Based Installation

Patchwork provides a Vagrantfile that can be used to quickly configure
Patchwork in a development environment. Like any Vagrant VM, you can start this
using the `vagrant up` command:

    $ cd patchwork  # the path to the repo you cloned above
    $ vagrant up

Once stacked, follow the on-screen instructions. For more information on
Vagrant itself, please refer to the [Vagrant documentation](ref-vagrant).

Alternatively, manual installation steps are provided below.

## Install Required Packages

There are a number of different requirements for developing Patchwork:

* Python and libraries
* A supported RDBMS

These are detailed below.

### Python Requirements

To develop Python-based software you first need Python. Patchwork supports
both Python 2.7 and Python 3.3+. One of these will be installed by default
on many installations, though they can also be installed manually using the
`python` or `python3` packages.

It's a good idea to use [virtual environments][ref-venv] to develop Python
software. Virtual environments are "instances" of your system Python without
any of the additional Python packages installed. They are useful to develop and
possibly deploy Patchwork against a "well known" set of dependencies, but they
can also be used to test Patchwork against several versions of Django.

If you do not have `virtualenv` installed then you should install it now. This
can be installed using the `python-virtualenv` or `python3-virtualenv`
packages. Alternatively you can install these using `pip`.

It is also helpful to install [`tox`][ref-tox] which is used for running tests
in Patchwork. This can be installed using the `python-tox` or `python3-tox`
packages, or via `pip`.

### Database Requirements

If not already installed, you may need to install an RDBMS. You can use either
MariaDB/MySQL or PostgreSQL for this purpose. You should also install the
development headers, known as `libmysqlclient-dev` or `libpq-dev` respectively
on Debian-based Debian-based distros like Ubuntu and `mysql-devel` or
`postgresql-devel` on RHEL-based distros.

**NOTE:** While Django provides support for
[multiple database backends][ref-django-db], Patchwork itself is only tested
against MySQL/MariaDB and PostgreSQL. Should you wish to use a different
backend, ensure you validate this first (and perhaps
[upstream][doc-contributing] any changes you may find necessary).

**NOTE:** You may be tempted to use SQLite to develop Patchwork. We'd advise
against doing this. SQLite supports a subset of the functionality of "full"
RDBMS like MySQL: for example, case-sensitive matching of Unicode
[is not supported][ref-sqlite-utf8]. You will find some tests provided by
Patchwork fail and some patches you develop may fail in production due to these
differences.

### Example Installations

An example for installing all these packages and the MySQL RDBMS on Ubuntu
15.04 is given below:

    $ sudo apt-get install python python-pip python-dev python-virtualenv \
        python-tox mysql-server libmysqlclient-dev

If you have an existing MariaDB/MySQL installation and have installed `pip`
already/are using [Python 3.4+][ref-py34-pip] then you can install all
packages using `pip`:

    $ sudo pip install virtualenv tox

If you wish to use Python 3 then simply replace 'python' with 'python3' in
the above command.

## Configure Virtual Environment

**NOTE:** If you are interested in simply [testing Patchwork][doc-testing],
many of the below steps are not required. tox will automatically install
dependencies and use virtual environments when testing.

Once these requirements are installed, you should create and activate a new
virtual environment. This can be done like so:

    $ virtualenv .venv
    $ source .venv/bin/activate
    (.venv)$

**NOTE:** It you installed a Python 3.x-based virtual environment package,
adjust the executable indicated above as necessary, e.g. `virtualenv-3.4`.

Now install the packages. Patchwork provides three requirements files.

* `requirements-dev.txt`: Packages required to configure a development
  environment
* `requirements-prod.txt`: Packages required for deploying Patchwork in
  production
* `requirements-test.txt`: Packages required to run tests

We're going to install the first of these, which can be done like so:

    (.venv)$ cd patchwork
    (.venv)$ pip install -r requirements-dev.txt

**NOTE:** Once configured this does not need to be done again *unless* the
requirements change, e.g. Patchwork requires an updated version of Django.

## Initialize the Database

One installed, the database must be configured. We will assume you have root
access to the database for these steps.

To begin, export your database credentials as follows:

    (.venv)$ db_user=root
    (.venv)$ db_pass=password

Now, create the database. If this is your first time configuring the database,
you must create a `patchwork` user (or similar) along with the database
instance itself. The commands below will do this, dropping existing databases
if necessary:

    (.venv)$ mysql -u$db_user -p$db_pass << EOF
    DROP DATABASE IF EXISTS patchwork;
    CREATE DATABASE patchwork CHARACTER SET utf8;
    GRANT ALL PRIVILEGES ON patchwork.* TO 'patchwork'@'localhost'
        IDENTIFIED BY 'password';
    EOF

**NOTE:** The `patchwork` username and `password` password are the defaults
expected by the provided `dev` settings files. If using something different,
please export the `PW_TEST_DB_USER` and `PW_TEST_DB_PASS` variables described
in the [Environment Variables](#environment-variables) section below.
Alternatively, you can create your own settings file with these variables
hardcoded and change the value of `DJANGO_SETTINGS_MODULE` as described below.

## Load Initial Data

Before continuing, we need to tell Django where it can find our configuration.
Patchwork provides a default development `settings.py` file for this purpose.
To use this, export the `DJANGO_SETTINGS_MODULE` environment variable as
described below:

    (.venv)$ export DJANGO_SETTINGS_MODULE=patchwork.settings.dev

Alternatively you can provide your own `settings.py` file and provide the path
to that instead.

Once done, we need to create the tables in the database. This can be done using
the `migrate` command of the `manage.py` executable:

    (.venv)$ ./manage.py migrate

Next, you should load the initial fixtures into Patchwork. These initial
fixtures provide.

* `default_tags.xml`: The tags that Patchwork will extract from mails.
  Examples: `Acked-By`, `Reviewed-By`
* `default_states.xml`: The states that a patch can be in. Examples:
  `Accepted`, `Rejected`
* `default_projects.xml`: A default project that you can then upload patches
  for

These can be loaded using the `loaddata` command:

    (.venv)$ ./manage.py loaddata default_tags default_states default_projects

You should also take the opportunity to create a "superuser". You can do this
using the aptly-named `createsuperuser` command:

    (.venv)$ ./manage.py createsuperuser

Once this is done, it's beneficial to load some real emails into the system.
This can be done manually, however it's generally much easier to download
an archive from a Mailman instance and load these using the `parsearchive.py`
tool. You can do this like so:

    (.venv)$ mm_user=myusername
    (.venv)$ mm_pass=mypassword
    (.venv)$ mm_host=https://lists.ozlabs.org
    (.venv)$ mm_url=$mm_host/private/patchwork.mbox/patchwork.mbox
    (.venv)$ curl -F username=$mm_user -F password=$mm_pass -k -O $mm_url

Where `mm_user` and `mm_pass` are the username and password you have registered
with on the Mailman instance found at `mm_host`.

**NOTE:** We provide instructions for downloading archives from the Patchwork
mailing list, but almost any instance of Mailman will allow downloading of
archives as seen above; simply change the `pw_url` variable defined. You can
find more informations about this [here][ref-mman-bulk].

Load these archives into Patchwork. Depending on the size of the downloaded
archives this may take some time:

    (.venv)$ PYTHONPATH=. ./patchwork/bin/parsearchive.py \
      --list-id=patchwork.ozlabs.org patchwork.mbox

Finally, run the server and browse to the IP address of your board using your
browser of choice:

    (.venv)$ ./manage.py runserver 0.0.0.0:8000

Once finished, you can kill the server (`Ctrl` + `C`) and exit the virtual
environment:

    (.venv)$ deactivate
    $

Should you wish to re-enter this environment, simply source the `activate`
script again.

## Django Debug Toolbar

Patchwork installs and enables the 'Django Debug Toolbar' by default. However,
by default this is only displayed if you are developing on localhost. If
developing on a different machine, you should configure an SSH tunnel such
that, for example, `localhost:8000` points to `[DEV_MACHINE_IP]:8000`.

## Environment Variables

The following environment variables are available to configure settings when
using the provided `dev` settings file.

<dl>
  <dt>PW_TEST_DB_NAME = 'patchwork'</dt>
  <dd>Name of the database</dd>
  <dt>PW_TEST_DB_USER = 'patchwork'</dt>
  <dd>Username to access the database with</dd>
  <dt>PW_TEST_DB_PASS = 'password'</dt>
  <dd>Password to access the database with</dd>
  <dt>PW_TEST_DB_TYPE = 'mysql'</dt>
  <dd>Type of database to use. Options: 'mysql', 'postgres'</dd>
</dl>

[doc-contributing]: ../CONTRIBUTING.md
[doc-deployment]: development.md
[doc-testing]: testing.md
[ref-django-db]: https://docs.djangoproject.com/en/1.8/ref/databases/
[ref-mman-bulk]: http://blog.behnel.de/posts/indexp118.html
[ref-py34-pip]: http://legacy.python.org/dev/peps/pep-0453/
[ref-sqlite-utf8]: https://www.sqlite.org/faq.html#q18
[ref-tox]: https://tox.readthedocs.org/en/latest/
[ref-vagrant]: https://www.vagrantup.com/docs/getting-started/
[ref-venv]: https://virtualenv.readthedocs.org/en/latest/
