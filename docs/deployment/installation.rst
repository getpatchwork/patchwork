Installation
============

This document describes the necessary steps to configure Patchwork in a
production environment. This requires a significantly "harder" deployment than
the one used for development. If you are interested in developing Patchwork,
refer to the :doc:`development guide </development/installation>` instead.

This document describes a single-node installation of Patchwork, which will
handle the database, server, and application. It is possible to split this into
multiple servers, which would provide additional scalability and availability,
but this is is out of scope for this document.


Deployment Guides, Provisioning Tools and Platform-as-a-Service
---------------------------------------------------------------

Before continuing, it's worth noting that Patchwork is a Django application.
With the exception of the handling of incoming mail (described below), it can
be deployed like any other Django application. This means there are tens, if
not hundreds, of existing articles and blogs detailing how to deploy an
application like this. As such, if any of the below information is unclear then
we'd suggest you go search for "Django deployment guide" or similar, deploy
your application, and submit a patch for this guide to clear up that confusion
for others.

You'll also find that the same search reveals a significant number of existing
deployment tools aimed at Django. These tools, be they written in Ansible,
Puppet, Chef or something else entirely, can be used to avoid much of the
manual configuration described below. If possible, embrace these tools to make
your life easier.

Finally, many Platform-as-a-Service (PaaS) providers and tools support
deployment of Django applications with minimal effort. Should you wish to avoid
much of the manual configuration, we suggest you investigate the many options
available to find one that best suits your requirements. The only issue here
will likely be the handling of incoming mail - something which many of these
providers don't support. We address this in the appropriate section below.


Requirements
------------

For the purpose of this guide, we will assume an **Ubuntu 20.04** host:
commands, package names and/or package versions will likely change if using a
different distro or release. Similarly, usage of different package versions to
the ones suggested may require slightly different configuration.

Before beginning, you should update and restart this system:

.. code-block:: shell

   $ sudo apt-get update -y
   $ sudo apt-get upgrade -y
   $ sudo reboot

Once rebooted, we need to configure some environment variables. These will be
used to ease deployment:

``DATABASE_NAME=patchwork``
  Name of the database. We'll name this after the application itself.

``DATABASE_USER=www-data``
  Username that the Patchwork web application will access the database with. We
  will use ``www-data``, for reasons described later in this guide.

``DATABASE_PASS=``
  Password that the Patchwork web application will access the database with. As
  we're going to use *peer* authentication (more on this later), this will be
  unset.

``DATABASE_HOST=``
  IP or hostname of the database host. As we're hosting the application on the
  same host as the database and hoping to use *peer* authentication, this will
  be unset.

``DATABASE_PORT=``
  Port of the database host. As we're hosting the application on the same host
  as the database and using the default configuration, this will be unset.

Export each of these. For example:

.. code-block:: shell

   $ export DATABASE_NAME=patchwork

The remainder of the requirements are listed as we install and configure the
various components required.


Database
--------

Install Requirements
~~~~~~~~~~~~~~~~~~~~

We're going to rely on PostgreSQL, though MySQL is also supported:

.. code-block:: shell

   $ sudo apt-get install -y postgresql postgresql-contrib

Configure Database
~~~~~~~~~~~~~~~~~~

We need to create a database for the system using the database name above. In
addition, we need to add database users for two system users, the web user (the
user that the web server runs as) and the mail user (the user that the mail
server runs as). On Ubuntu these are ``www-data`` and ``nobody``, respectively.
PostgreSQL supports `peer`__ authentication, which uses the standard UNIX
authentication method as a backend. This means no database-specific passwords
need to be configured.

PostgreSQL created a system user called ``postgres``; you will need to run
commands as this user.

.. code-block:: shell

   $ sudo -u postgres createdb $DATABASE_NAME
   $ sudo -u postgres createuser $DATABASE_USER
   $ sudo -u postgres createuser nobody

We will also need to apply permissions to the tables in this database but
seeing as the tables haven't actually been created yet this will have to be
done later.

__ https://www.postgresql.org/docs/10/static/auth-methods.html#AUTH-PEER

.. note::

    As noted in the `Django documentation`__, Django expects databases to be
    configured with an encoding of UTF-8 or UTF-16. If using MySQL, you may
    need to configure this this explicitly as older versions defaulted to
    `latin1` encoding. Refer to the `MySQL documentation`__ for more
    information.

    __ https://docs.djangoproject.com/en/3.1/ref/unicode/
    __ https://dev.mysql.com/doc/refman/en/charset.html


Patchwork
---------

Install Requirements
~~~~~~~~~~~~~~~~~~~~

The first requirement is Patchwork itself. It can be downloaded like so:

.. code-block:: shell

   $ wget https://github.com/getpatchwork/patchwork/archive/v3.0.0.tar.gz

We will install this under ``/opt``, though this is only a suggestion:

.. code-block:: shell

   $ tar -xvzf v3.0.0.tar.gz
   $ sudo mv patchwork-3.0.0 /opt/patchwork

.. important::

   Per the `Django documentation`__, source code should not be placed in your
   web server's document root as this risks the possibility that people may be
   able to view your code over the Web. This is a security risk.

   __ https://docs.djangoproject.com/en/2.2/intro/tutorial01/#creating-a-project

Next we require Python. If not already installed, then you should do so now.
Patchwork supports Python 3.6+. Python 3 is installed by default, but you
should validate this now:

.. code-block:: shell

   $ sudo apt-get install -y python3

We also need to install the various requirements. Let's use system packages for
this also:

.. code-block:: shell

   $ sudo apt-get install -y python3-django python3-psycopg2 \
       python3-djangorestframework python3-django-filters

.. tip::

   The `pkgs.org <https://pkgs.org/>`__ website provides a great reference for
   identifying the name of these dependencies.

You can also install requirements using *pip*. If using this method, you can
install requirements like so:

.. code-block:: shell

   $ sudo pip install -r /opt/patchwork/requirements-prod.txt

.. _deployment-settings:

Configure Patchwork
~~~~~~~~~~~~~~~~~~~

You will also need to configure a `settings file`__ for Django. A sample
settings file is provided that defines default settings for Patchwork. You'll
need to configure settings for your own setup and save this as
``production.py``.

.. code-block:: shell

   $ cd /opt/patchwork
   $ cp patchwork/settings/production{.example,}.py

Alternatively, you can override the ``DJANGO_SETTINGS_MODULE`` environment
variable and provide a completely custom settings file.

The provided ``production.example.py`` settings file is configured to read
configuration from environment variables. This suits container-based
deployments quite well but for the all-in-one deployment we're configuring
here, hardcoded settings makes more sense. If you wish to use environment
variables, you should export each setting using the appropriate name, such as
``DJANGO_SECRET_KEY``, ``DATABASE_NAME`` or ``EMAIL_HOST``, instead of
modifying the ``production.py`` file as we've done below.

__ https://docs.djangoproject.com/en/2.2/ref/settings/

Databases
^^^^^^^^^

We already defined most of the configuration necessary for this in the intro.
As a reminder, these were:

- ``DATABASE_NAME``
- ``DATABASE_USER``
- ``DATABASE_PASSWORD``
- ``DATABASE_HOST``
- ``DATABASE_PORT``

Export these environment variables or configure the ``DATABASE`` setting in
``production.py`` accordingly.

Static Files
^^^^^^^^^^^^

While we have not yet configured our proxy server, we need to configure the
location that these files will be stored in. We will install these under
``/var/www/patchwork``, though this is only a suggestion and can be changed.

.. code-block:: shell

   $ sudo mkdir -p /var/www/patchwork

Export the ``STATIC_ROOT`` environment variable or configure the
``STATIC_ROOT`` setting in ``production.py``.

.. code-block:: python

   STATIC_ROOT = '/var/www/patchwork'

Secret Key
^^^^^^^^^^

The ``SECRET_KEY`` setting is necessary for Django to generate signed data.
This should be a random value and kept secret. You can generate and a value for
``SECRET_KEY`` with the following Python code:

.. code-block:: python

   import string
   import secrets

   chars = string.ascii_letters + string.digits + string.punctuation
   print("".join([secrets.choice(chars) for i in range(50)]))

Export the ``DJANGO_STATIC_KEY`` environment variable or configure the
``STATIC_KEY`` setting in ``production.py``.

Other Options
^^^^^^^^^^^^^

There are many other settings that may be configured, many of which are
described in :doc:`configuration`.

* ``ADMINS``
* ``TIME_ZONE``
* ``LANGUAGE_CODE``
* ``DEFAULT_FROM_EMAIL``
* ``NOTIFICATION_FROM_EMAIL``

These are not configurable using environment variables and must be configured
directly in the ``production.py`` settings file instead. For example, if you
wish to enable the XML-RPC API, you should add the following:

.. code-block:: python

   ENABLE_XMLRPC = True

Similarly, should you wish to disable the REST API, you should add the
following:

.. code-block:: python

   ENABLE_REST_API = False

For more information, refer to :doc:`configuration`.

Final Steps
~~~~~~~~~~~

Once done, we should be able to check that all requirements are met using the
``check`` command of the ``manage.py`` executable. This must be run as the
``www-data`` user:

.. code-block:: shell

   $ sudo -u www-data python3 manage.py check

.. note::

   If you've been using environment variables to configure your deployment,
   you must pass the ``--preserve-env`` option for each attribute or pass the
   environments as part of the command:

   .. code-block:: shell

      $ sudo -u www-data \
          --preserve-env=DATABASE_NAME \
          --preserve-env=DATABASE_USER \
          --preserve-env=DATABASE_PASS \
          --preserve-env=DATABASE_HOST \
          --preserve-env=DATABASE_PORT \
          --preserve-env=STATIC_ROOT \
          --preserve-env=DJANGO_SECRET_KEY \
      python3 manage.py check

We should also take this opportunity to both configure the database and static
files:

.. code-block:: shell

   $ sudo -u www-data python3 manage.py migrate
   $ sudo python3 manage.py collectstatic
   $ sudo -u www-data python3 manage.py loaddata default_tags default_states

.. note::

   The above ``default_tags`` and ``default_states`` fixtures above are just
   that: defaults. You can modify these to fit your own requirements.

Finally, it may be helpful to start the development server quickly to ensure
you can see *something*. For this to function, you will need to add the
``ALLOWED_HOSTS`` and ``DEBUG`` settings to the ``production.py`` settings
file:

.. code-block:: python

   ALLOWED_HOSTS = ['*']
   DEBUG = True

Now, run the server.

.. code-block:: shell

   $ sudo -u www-data python3 manage.py runserver 0.0.0.0:8000

Browse this instance at ``http://[your_server_ip]:8000``. If everything is
working, kill the development server using :kbd:`Control-c` and remove
``ALLOWED_HOSTS`` and ``DEBUG``.


Reverse Proxy and WSGI HTTP Servers
-----------------------------------

Install Packages
~~~~~~~~~~~~~~~~

We will use *nginx* and *uWSGI* to deploy Patchwork, acting as reverse proxy
server and WSGI HTTP server respectively. Other options are available, such as
*Apache* with the *mod_wsgi* module, or *nginx* with the *Gunicorn* WSGI HTTP
server. While we don't document these, sample configuration files for the
former case are provided in ``lib/apache2/``.

Let's start by installing *nginx* and *uWSGI*:

.. code-block:: shell

   $ sudo apt-get install -y nginx-full uwsgi uwsgi-plugin-python3

Configure nginx and uWSGI
~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration files for *nginx* and *uWSGI* are provided in the ``lib``
subdirectory of the Patchwork source code. These can be modified as necessary,
but for now we will simply copy them.

First, let's load the provided configuration for *nginx* and disable the
default configuration:

.. code-block:: shell

   $ sudo cp /opt/patchwork/lib/nginx/patchwork.conf \
       /etc/nginx/sites-available/
   $ sudo unlink /etc/nginx/sites-enabled/default

If you wish to modify this configuration, now is the time to do so. Once done,
validate and enable your configuration:

.. code-block:: shell

   $ sudo ln -s /etc/nginx/sites-available/patchwork.conf \
       /etc/nginx/sites-enabled/patchwork.conf
   $ sudo nginx -t

Now, use the provided configuration for *uWSGI*:

.. code-block:: shell

   $ sudo mkdir -p /etc/uwsgi/sites
   $ sudo cp /opt/patchwork/lib/uwsgi/patchwork.ini \
       /etc/uwsgi/sites/patchwork.ini

.. note::

   We created the ``/etc/uwsgi`` directory above because we're going to run
   *uWSGI* in `emperor mode`__. This has benefits for multi-app deployments.

.. note::

   If you're using environment variables for configuration, you will need to
   edit the ``patchwork.ini`` file created above to include these using the
   ``env = VAR=VALUE`` syntax.

__ https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html

Configure Patchwork
~~~~~~~~~~~~~~~~~~~

For `security reasons`__, Django requires you to configure the
``ALLOWED_HOSTS`` setting, which is a "list of strings representing the
host/domain names that this Django site can serve". To do this, configure the
setting in the ``production.py`` setting file using the hostname(s) and/or IP
address(es) from which you will be serving this domain. For example:

.. code-block:: python

   ALLOWED_HOSTS = ('.example.com', )

__ https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts

Create systemd Unit File
~~~~~~~~~~~~~~~~~~~~~~~~

As things stand, *uWSGI* will need to be started manually every time the system
boots, in addition to any time it may fail. We can automate this process using
*systemd*. To this end a `systemd unit file`__ should be created to start
*uWSGI* at boot:

.. code-block:: shell

   $ sudo tee /etc/systemd/system/uwsgi.service > /dev/null << EOF
   [Unit]
   Description=uWSGI Emperor service

   [Service]
   ExecStartPre=/bin/bash -c 'mkdir -p /run/uwsgi; chown www-data:www-data /run/uwsgi'
   ExecStart=/usr/bin/uwsgi --emperor /etc/uwsgi/sites
   Restart=always
   KillSignal=SIGQUIT
   Type=notify
   NotifyAccess=all

   [Install]
   WantedBy=multi-user.target
   EOF

You should also delete the default service file found in ``/etc/init.d`` to
ensure the unit file defined above is used.

.. code-block:: shell

   sudo rm /etc/init.d/uwsgi
   sudo systemctl daemon-reload

__ https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html

.. _deployment-final-steps:

Final Steps
~~~~~~~~~~~

Start the *uWSGI* service we created above:

.. code-block:: shell

   $ sudo systemctl restart uwsgi
   $ sudo systemctl status uwsgi
   $ sudo systemctl enable uwsgi

Next up, restart the *nginx* service:

.. code-block:: shell

   $ sudo systemctl restart nginx
   $ sudo systemctl status nginx
   $ sudo systemctl enable nginx

Finally, browse to the instance using your browser of choice. You may wish to
take this opportunity to setup your projects and configure your website address
(in the Sites section of the admin console, found at ``/admin``).

If there are issues with the instance, you can check the logs for *nginx* and
*uWSGI*. There are a couple of commands listed below which can help:

- ``sudo systemctl status uwsgi``, ``sudo systemctl status nginx``

  To ensure the services have correctly started

- ``sudo cat /var/log/nginx/error.log``

  To check for issues with *nginx*

- ``sudo cat /var/log/patchwork.log``

  To check for issues with *uWSGI*. This is the default log location set by the
  ``daemonize``  setting in the *uWSGI* configuration file.

Django administrative console
-----------------------------

In order to access the administrative console at ``/admin``, you need at least
one user account to be registered and configured as a super user or staff
account to access the Django administrative console.  This can be achieved by
doing the following:

.. code-block:: shell

   $ python3 manage.py createsuperuser

Once the administrative console is accessible, you would want to configure your
different sites and their corresponding domain names, which is required for the
different emails sent by Patchwork (registration, password recovery) as well as
the sample ``pwclientrc`` files provided by your project's page.

.. _deployment-parsemail:

Incoming Email
--------------

Patchwork is designed to parse incoming mails which means you need an address
to receive email at. This is a problem that has been solved for many web apps,
thus there are many ways to go about this. Some of these ways are discussed
below.

IMAP/POP3
~~~~~~~~~

The easiest option for getting mail into Patchwork is to use an existing email
address in combination with a mail retriever like `getmail`__, which will
download mails from your inbox and pass them to Patchwork for processing.
*getmail* is easy to set up and configure: to begin, you need to install it:

.. code-block:: shell

   $ sudo apt-get install -y getmail

Once installed, you should configure it, substituting your own configuration
details where required below:

.. code-block:: shell

   $ sudo tee /etc/getmail/use@example.com/getmailrc > /dev/null << EOF
   [retriever]
   type = SimpleIMAPSSLRetriever
   server = imap.example.com
   port = 993
   username = XXX
   password = XXX
   mailboxes = ALL

   [destination]
   # we configure Patchwork as a "mail delivery agent", in that it will
   # handle our mails
   type = MDA_external
   path = /opt/patchwork/patchwork/bin/parsemail.sh

   [options]
   # retrieve only new emails
   read_all = false
   # do not add a Delivered-To: header field
   delivered_to = false
   # do not add a Received: header field
   received = false
   EOF

Validate that this works as expected by starting *getmail*:

.. code-block:: shell

   $ getmail --getmaildir=/etc/getmail/user@example.com --idle INBOX

If everything works as expected, you can create a *systemd* script to ensure
this starts on boot:

.. code-block:: shell

   $ sudo tee /etc/systemd/system/getmail.service > /dev/null << EOF
   [Unit]
   Description=Getmail for user@example.com

   [Service]
   User=nobody
   ExecStart=/usr/bin/getmail --getmaildir=/etc/getmail/user@example.com --idle INBOX
   Restart=always

   [Install]
   WantedBy=multi-user.target
   EOF

And start the service:

.. code-block:: shell

   $ sudo systemctl start getmail
   $ sudo systemctl status getmail
   $ sudo systemctl enable getmail

__ http://pyropus.ca/software/getmail/

Mail Transfer Agent (MTA)
~~~~~~~~~~~~~~~~~~~~~~~~~

The most flexible option is to configure our own mail transfer agent (MTA) or
"email server". There are many options, of which `Postfix`__ is one.  While we
don't cover setting up Postfix here (it's complicated and there are many guides
already available), Patchwork does include a script to take received mails and
create the relevant entries in Patchwork for you. To use this, you should
configure your system to forward all emails to a given localpart (the bit
before the ``@``) to this script. Using the ``patchwork`` localpart (e.g.
``patchwork@example.com``) you can do this like so:

.. code-block:: shell

   $ sudo tee -a /etc/aliases > /dev/null << EOF
   patchwork: "|/opt/patchwork/patchwork/bin/parsemail.sh"
   EOF

You should ensure the appropriate user is created in PostgreSQL and that it has
(minimal) access to the database. Patchwork provides scripts for the latter and
they can be loaded as seen below:

.. code-block:: shell

   $ sudo -u postgres psql -f \
       /opt/patchwork/lib/sql/grant-all.postgres.sql patchwork

.. note::

   This assumes that you are using the aliases(5) file that is owned by root,
   and that Postfix's ``default_privs`` configuration is set as ``nobody``. If
   this is not the case, you should change both the username in the ``createuser``
   command above and substitute the username in the ``grant-all.postgres.sql``
   script with the appropriate alternative.

__ http://www.postfix.org/

Use a Email-as-a-Service Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Setting up an email server can be a difficult task and, in the case of
deployment on PaaS provider, may not even be an option. In this case, there
are a variety of web services available that offer "Email-as-as-Service".
These services typically convert received emails into HTTP POST requests to
your endpoint of choice, allowing you to sidestep configuration issues. We
don't cover this here, but a simple wrapper script coupled with one of these
services can be more than to get email into Patchwork.

You can also create such as service yourself using a PaaS provider that
supports incoming mail and writing a little web app.


.. _deployment-vcs:

(Optional) Configure your VCS to Automatically Update Patches
-------------------------------------------------------------

The ``tools`` directory of the Patchwork distribution contains a file named
``post-receive.hook`` which is a sample Git hook that can be used to
automatically update patches to the *Accepted* state when corresponding commits
are pushed via Git.

To install this hook, simply copy it to the ``.git/hooks`` directory on your
server, name it ``post-receive``, and make it executable.

This sample hook has support to update patches to different states depending on
which branch is being pushed to. See the ``STATE_MAP`` setting in that file.

If you are using a system other than Git, you can likely write a similar hook
using the :doc:`APIs </api/index>` or :doc:`API clients </usage/clients>` to to
update patch state. If you do write one, please contribute it.


.. _deployment-cron:

(Optional) Configure the Patchwork Cron Job
-------------------------------------------

Patchwork can send notifications of patch changes. Patchwork uses a cron
management command - ``manage.py cron`` - to send these notifications and to
clean up expired registrations. To enable this functionality, add the following
to your crontab::

   # m h  dom mon dow   command
   */10 * * * * cd patchwork; python3 ./manage.py cron

.. note::

   The frequency should be the same as the ``NOTIFICATION_DELAY_MINUTES``
   setting, which defaults to 10 minutes. Refer to the :doc:`configuration
   guide <configuration>` for more information.
