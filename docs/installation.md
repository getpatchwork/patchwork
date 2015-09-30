# Deploying Patchwork

Patchwork uses the Django framework - there is some background on deploying
Django applications here:

    http://www.djangobook.com/en/2.0/chapter12/

You'll need the following (applications used for patchwork development are
in brackets):

 * A Python interpreter
 * [Django] >= 1.6. The latest version is recommended
 * A webserver and suitable WSGI plugin. Options include [Apache] with the
   [mod_python] plugin, or [Gunicorn] with [nginx] as the proxy server
 * A database server (PostgreSQL, MySQL)
 * Relevant Python modules for the database server (see the various
   [requirements.txt] files)

[Django]: https://www.djangoproject.com/
[Apache]: http://httpd.apache.org/
[mod_python]: http://modpython.org/
[Gunicorn]: http://gunicorn.org/
[nginx]: http://nginx.org/
[requirements.txt]: ./docs

## Database Configuration

Django's ORM support multiple database backends, though the majority of testing
has been carried out with PostgreSQL and MySQL.

We need to create a database for the system, add accounts for two system users:
the web user (the user that your web server runs as) and the mail user (the
user that your mail server runs as). On Ubuntu these are `www-data` and
`nobody`, respectively.

As an alternative, you can use password-based login and a single database
account. This is described further down.

**NOTE:** For the following commands, a `$` prefix signifies that the command
should be entered at your shell prompt, and a `>` prefix signifies the
command-line client for your SQL server (`psql` or `mysql`).

### Install Packages

If you don't already have MySQL installed, you'll need to do so now. For
example, to install MySQL on RHEL:

    $ sudo yum install mysql-server

### Create Required Databases and Users

#### PostgreSQL (ident-based)

PostgreSQL support [ident-based authentication], which uses the standard UNIX
authentication method as a backend. This means no database-specific passwords
need to be set/used. Assuming you are using this form of authentication, you
just need to create the relevant UNIX users and database:

    $ createdb patchwork
    $ createuser www-data
    $ createuser nobody

[ident-based authentication]: http://www.postgresql.org/docs/8.4/static/auth-methods.html#AUTH-IDENT

#### PostgreSQL (password-based)

If you are not using the ident-based authentication, you will need to create
both a new database and a new database user:

    $ createuser -PE patchwork
    $ createdb -O patchwork patchwork

#### MySQL

    $ mysql
    > CREATE DATABASE patchwork CHARACTER SET utf8;
    > CREATE USER 'www-data'@'localhost' IDENTIFIED BY '<password>';
    > CREATE USER 'nobody'@'localhost' IDENTIFIED BY '<password>';

### Configure Settings

Once that is done, you need to tell Django about the new database settings,
by defining your own `production.py` settings file (see below). For PostgreSQL:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': 'localhost',
            'PORT': '',
            'USER': 'patchwork',
            'PASSWORD': 'my_secret_password',
            'NAME': 'patchwork',
            'TEST_CHARSET': 'utf8',
        },
    }

If you're using MySQL, only the `ENGINE` changes:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            ...
        },
    }

**NOTE:** `TEST_CHARSET` (`TEST/CHARSET` in Django >= 1.7) is used when
creating tables for the test suite. Without it, tests checking for the correct
handling of non-ASCII characters fail.

## Django Setup

### Configure Directories

Set up some initial directories in the patchwork base directory:

    mkdir -p lib/packages lib/python

`lib/packages` is for stuff we'll download, `lib/python` is to add to our
Python path. We'll symlink Python modules into `lib/python`.

At the time of release, patchwork depends on Django version 1.6 or later.
Where possible, try to use the latest stable version (currently 1.8). Your
distro probably provides this. If not, install it manually:

    cd lib/packages
    git clone https://github.com/django/django.git -b stable/1.8.x
    cd ../python
    ln -s ../packages/django/django ./django

### Configure Settings

You will also need to configure a [settings] file for Django. A
[sample settings file] is provided, which defines default settings for
patchwork. You'll need to configure settings for your own setup and save this
as `production.py` (or override the `DJANGO_SETTINGS_MODULE` environment
variable).

    cp patchwork/settings/production.example.py \
      patchwork/settings/production.py

At the very minimum, the following settings need to be configured:

    SECRET_KEY
    ADMINS
    TIME_ZONE
    LANGUAGE_CODE
    DEFAULT_FROM_EMAIL
    NOTIFICATION_FROM_EMAIL

You can generate the `SECRET_KEY` with the following python code:

    import string, random
    chars = string.letters + string.digits + string.punctuation
    print repr("".join([random.choice(chars) for i in range(0,50)]))

If you wish to enable the XML-RPC interface, add the following to the file:

    ENABLE_XMLRPC = True

### Configure Database Tables

Then, get patchwork to create its tables in your configured database. For
Django 1.6 and below:

    PYTHONPATH=../lib/python ./manage.py syncdb

For Django 1.7+:

    PYTHONPATH=../lib/python ./manage.py migrate

Add privileges for your mail and web users. This is only needed if you use the
ident-based approach. If you use password-based database authentication, you
can skip this step.

For Postgresql:

    psql -f lib/sql/grant-all.postgres.sql patchwork

For MySQL:

    mysql patchwork < lib/sql/grant-all.mysql.sql

### Other Tasks

You will need to collect the static content into one location from which
it can be served (by Apache or nginx, for example):

    PYTHONPATH=lib/python ./manage.py collectstatic

You'll also need to load the initial tags and states into the patchwork
database:

    PYTHONPATH=lib/python ./manage.py loaddata default_tags default_states

[sample_settings_file]: ../patchwork/settings/production.example.py
[settings]: https://docs.djangoproject.com/en/1.8/topics/settings/

## Apache Setup

Example apache configuration files are in `lib/apache2/`.

### wsgi

django has built-in support for WSGI, which supersedes the fastcgi handler. It is thus the preferred method to run patchwork.

The necessary configuration for Apache2 may be found in:

    lib/apache2/patchwork.wsgi.conf.

You will need to install/enable mod_wsgi for this to work:

    a2enmod wsgi
    apache2ctl restart

## Configure patchwork

Now, you should be able to administer patchwork, by visiting the URL:

    http://your-host/admin/

You'll probably want to do the following:

* Set up your projects
* Configure your website address (in the Sites section of the admin)

## Subscribe a Local Address to the Mailing List

You will need an email address for patchwork to receive email on - for example
- `patchwork@your-host`, and this address will need to be subscribed to the
list. Depending on the mailing list, you will probably need to confirm the
subscription - temporarily direct the alias to yourself to do this.

## Setup your MTA to Deliver Mail to the Parsemail Script

Your MTA will need to deliver mail to the parsemail script in the
email/directory. (Note, do not use the `parsemail.py` script directly).
Something like this in /etc/aliases is suitable for postfix:

    patchwork: "|/srv/patchwork/patchwork/bin/parsemail.sh"

You may need to customise the `parsemail.sh` script if you haven't installed
patchwork in `/srv/patchwork`.

Test that you can deliver a patch to this script:

    sudo -u nobody /srv/patchwork/patchwork/bin/parsemail.sh < mail

## Set up the patchwork cron script

Patchwork uses a cron script to clean up expired registrations, and send
notifications of patch changes (for projects with this enabled). Something like
this in your crontab should work:

    # m h  dom mon dow   command
    */10 * * * * cd patchwork; ./manage.py cron

The frequency should be the same as the `NOTIFICATION_DELAY_MINUTES` setting,
which defaults to 10 minutes.

## (Optional) Configure your VCS to Automatically Update Patches

The tools directory of the patchwork distribution contains a file named
`post-receive.hook` which is a sample git hook that can be used to
automatically update patches to the `Accepted` state when corresponding
commits are pushed via git.

To install this hook, simply copy it to the `.git/hooks` directory on your
server, name it `post-receive`, and make it executable.

This sample hook has support to update patches to different states depending
on which branch is being pushed to. See the `STATE_MAP` setting in that file.

If you are using a system other than git, you can likely write a similar hook
using `pwclient` to update patch state. If you do write one, please contribute
it.

Some errors:

* `ERROR: permission denied for relation patchwork_...`
  The user that patchwork is running as (i.e. the user of the web-server)
  doesn't have access to the patchwork tables in the database. Check that your
  web server user exists in the database, and that it has permissions to the
  tables.

* pwclient fails for actions that require authentication, but a username
and password is given int ~/.pwclient rc. Server reports "No authentication
credentials given".
  If you're using the FastCGI interface to apache, you'll need the
  `-pass-header Authorization` option to the FastCGIExternalServer
  configuration directive.
