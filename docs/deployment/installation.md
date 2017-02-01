# Deployment

This document describes the necessary steps to configure Patchwork in a
production environment. This requires a significantly "harder" deployment than
the one used for development. If you are interested in developing Patchwork,
please refer to [the development guide][doc-development] instead.

This document describes a two-node installation of Patchwork, consisting of
a database sever and an application server. It should be possible to combine
these machines for smaller Patchwork instances. It should also be possible to
configure high availability deployment through use of additional database and
application machines, though this is out of the scope of this document.

## Deployment Guides, Provisioning Tools and Platform-as-a-Service

Before continuing, it's worth noting that Patchwork is a Django application.
With the exception of the handling of incoming mail (described below), it
can be deployed like any other Django application. This means there are tens,
if not hundreds, of existing articles and blogs detailing how to deploy an
application like this. As such, if any of the below information is unclear
then we'd suggest you go search for "Django deployment guide" or similar,
deploy your application, and submit [a patch for this guide][doc-contributing]
to clear up that confusion for others.

You'll also find that the same search reveals a significant number of existing
deployment tools aimed at Django. These tools, be they written in Ansible,
Puppet, Chef or something else entirely, can be used to avoid much of the
manual configuration described below. If possible, embrace these tools to make
your life easier.

Finally, many Platform-as-a-Service (PaaS) providers and tools support
deployment of Django applications with minimal effort. Should you wish to
avoid much of the manual configuration, we suggest you investigate the many
options available to find one that best suits your requirements. The only issue
here will likely be the handling of incoming mail - something which many of
these providers don't support. We address this in the appropriate section
below.

## Requirements

For the purpose of this guide, we will assume the following machines:

| server role | IP address |
|-------------|------------|
| database    | 10.1.1.1   |
| application | 10.1.1.2   |

We will use the database server to, ostensibly enough, host the database for
the Patchwork instance. The application server, on the other hand, will host
the Patchwork instance along with the required reverse proxy and WSGI HTTP
servers.

We expect a Ubuntu 15.04 installation on each of these hosts: commands,
package names and/or package versions will likely change if using a
different distro or release. In addition, usage of different package versions
to the ones suggested may require slightly different configuration.

Before beginning, you should update these systems:

    $ sudo apt-get update
    $ sudo apt-get upgrade

We also need to configure some environment variables to ease deployment. These
should be exported on all systems:

<dl>
  <dt>PW_HOST_DB=10.1.1.1</dt>
  <dd>IP of the database host</dd>
  <dt>PW_HOST_APP=10.1.1.2</dt>
  <dd>IP of the application host</dd>
  <dt>PW_DB_NAME=patchwork</dt>
  <dd>Name of the database</dd>
  <dt>PW_DB_USER=www-data</dt>
  <dd>Username that the Patchwork app will access the database with</dd>
</dl>

## Database

These steps should be run on the database server.

**NOTE:** If you already have a database server on site, you can skip much of
this section.

### Install Requirements

We're going to rely on PostgreSQL. You can adjust the below steps if using a
different RDBMS. Install the required packages.

    $ sudo apt-get install -y postgresql postgresql-contrib

### Configure Database

PostgreSQL created a user account called `postgres`; you will need to run
commands as this user. Use this account to create the database that Patchwork
will use, using the credentials we configured earlier.

    $ sudo -u postgres createdb $PW_DB_NAME
    $ sudo -u postgres createuser $PW_DB_USER

We will also need to apply permissions to the tables in this database but
seeing as the tables haven't actually been created yet this will have to be
done later.

**TODO** `pg_hba.conf` configuration

## Patchwork

These steps should be run on the application server.

### Install Packages

The first requirement is Patchwork itself. It can be downloaded like so:

    $ wget https://github.com/getpatchwork/patchwork/archive/v1.1.0.tar.gz

We will install this under `/opt`, though this is only a suggestion:

    $ tar -xvzf v1.1.0.tar.gz
    $ sudo mv v1.1.0 /opt/patchwork

**NOTE:** Per the [Django documentation][ref-django-files], source code should
not be placed in your web server's document root as this risks the possibility
that people may be able to view your code over the Web. This is a security
risk.

Next we require Python. If not already installed, then you should do so now.
Patchwork supports both Python 2.7 and Python 3.3+, though we would suggest
using the latter to ease future upgrades:

    $ sudo apt-get install python3  # or 'python' if using Python 2.7

We require a number of Python packages. These can be installed using `pip`:

    $ sudo pip install -r /opt/patchwork/requirements-prod.txt

If you're not using `pip`, you will need to identify and install the
corresponding distro package for each of these requirements. For example:

    $ sudo apt-get install python3-django

**NOTE:** The [pkgs.org][ref-pkgs] website provides a great reference for
identifying the name of these dependencies.

### Configure Patchwork

You will also need to configure a [settings][ref-django-settings] file for
Django. A sample settings file is provided that defines default settings for
Patchwork. You'll need to configure settings for your own setup and save this
as `production.py`.

    $ cp patchwork/settings/production.example.py \
        patchwork/settings/production.py

Alternatively, you can override the `DJANGO_SETTINGS_MODULE` environment
variable and provide a completely custom settings file.

**NOTE:** You should not include shell variables in settings but rather
hardcoded values. These settings files are evaluated in Python - not a shell.

### Databases

You can configure the `DATABASES` setting using the variables we set earlier.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': '$PW_HOST_DB',  # don't use sh variables but actual values
            'PORT': '',
            'NAME': '$PW_DB_NAME',
            'USER': '$PW_DB_USER',
            'PASSWORD': '$PW_DB_PASS',
            'TEST': {
                'CHARSET': 'utf8',
            },
        },
    }

**NOTE:** `TEST/CHARSET` is used when creating tables for the test suite.
Without it, tests checking for the correct handling of non-ASCII characters
fail. It is not necessary if you don't plan to run tests, however.

#### Static Files

While we have not yet configured our proxy server, we do need to configure
the location that these files will be stored in. We will install these under
`/var/www/patchwork`, though this is only a suggestion and can be changed.

    $ mkdir /var/www/patchwork

You can configure this by setting the `STATIC_ROOT` variable.

    STATIC_ROOT = '/var/www/patchwork'

#### Other Options

Finally, the following settings need to be configured. The purpose of these
variables is described in the [Django documentation][ref-django-settings]:

* `SECRET_KEY`
* `ADMINS`
* `TIME_ZONE`
* `LANGUAGE_CODE`
* `DEFAULT_FROM_EMAIL`
* `NOTIFICATION_FROM_EMAIL`

You can generate the `SECRET_KEY` with the following python code:

    import string, random
    chars = string.letters + string.digits + string.punctuation
    print repr("".join([random.choice(chars) for i in range(0,50)]))

If you wish to enable the XML-RPC interface, you should add the following to
the file:

    ENABLE_XMLRPC = True

### Final Steps

Once done, we should be able to check that all requirements are met using
the `check` command of the `manage.py` executable:

    $ /opt/patchwork/manage.py check

We should also take this opportunity to both configure the database and static
files:

    $ /opt/patchwork/manage.py migrate
    $ /opt/patchwork/manage.py loaddata \
        /opt/patchwork/patchwork/fixtures/default_tags.xml
    $ /opt/patchwork/manage.py loaddata \
        /opt/patchwork/patchwork/fixtures/default_states.xml
    $ /opt/patchwork/manage.py collectstatic

**NOTE:** The above `default_tags` and `default_states` are just that:
defaults. You can modify these to fit your own requirements.

Finally, it may be helpful to start the development server quickly to ensure
you can see *something*:

    $ /opt/patchwork/manage.py runserver 0.0.0.0:8080

Browse this instance at `http://[your_server_ip]:8000`. If everything is
working, kill the development server using `Ctrl`+`C`.

## Reverse Proxy and WSGI HTTP Servers

These steps should be run on the application server.

### Install Packages

We will use nginx and uWSGI to deploy Patchwork, acting as reverse proxy server
and WSGI HTTP server respectively. Other options are available, such as
Apache+mod_wsgi or nginx+Gunicorn. While we don't document these, sample
configuration files for the former case are provided in `lib/apache2/`.

    $ sudo apt-get install nginx-full uwsgi uwsgi-plugin-python

### Configure nginx and uWSGI

Configuration files for nginx and uWSGI are provided in the `lib` subdirectory
of the Patchwork source code. These can be modified as necessary, but for now
we will simply copy them.

First, let's load the provided configuration for nginx:

    $ sudo cp /opt/patchwork/lib/nginx/patchwork.conf \
        /etc/nginx/sites-available/

If you wish to modify this configuration, now is the time to do so. Once done,
validate and enable your configuration:

    $ sudo nginx -t
    $ sudo ln -s /etc/nginx/sites-available/patchwork.conf \
        /etc/nginx/sites-enabled/patchwork.conf

Now use the provided configuration for uWSGI:

    $ sudo mkdir -p /etc/uwsgi/sites
    $ sudo cp /opt/patchwork/lib/uwsgi/patchwork.ini \
        /etc/uwsgi/sites/patchwork.ini

**NOTE** We created the `/etc/uwsgi` directory above because we're going to run
uWSGI in ["emperor mode][ref-uwsgi-emperor]". This has benefits for multi-app
deployments.

### Create systemd Unit File

As things stand, uWSGI will need to be started manually every time the system
boots, in addition to any time it may fail. We can automate this process using
systemd. To this end a [systemd unit file][ref-uwsgi-systemd] should be created
to start uWSGI at boot:

    $ sudo cat << EOF > /etc/systemd/system/uwsgi.service
    [Unit]
    Description=uWSGI Emperor service

    [Service]
    ExecStartPre=/usr/bin/bash -c 'mkdir -p /run/uwsgi; chown user:nginx /run/uwsgi'
    ExecStart=/usr/bin/uwsgi --emperor /etc/uwsgi/sites
    Restart=always
    KillSignal=SIGQUIT
    Type=notify
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target
    EOF

**NOTE:** On older version of Ubuntu you may need to tweak these steps to use
[upstart][ref-uwsgi-upstart] instead.

### Final Steps

Start the uWSGI service we created above:

    $ sudo systemctl start uwsgi
    $ sudo systemctl status uwsgi

Next up, restart the nginx service:

    $ sudo systemctl restart nginx
    $ sudo systemctl status nginx

Patchwork uses a cron script to clean up expired registrations and send
notifications of patch changes (for projects with this enabled). Something like
this in your crontab should work.

    # m h  dom mon dow   command
    */10 * * * * cd patchwork; ./manage.py cron

**NOTE**: The frequency should be the same as the `NOTIFICATION_DELAY_MINUTES`
setting, which defaults to 10 minutes.

Finally, browse to the instance using your browser of choice.

You may wish to take this opportunity to setup your projects and configure your
website address (in the Sites section of the admin console, found at `/admin`).

## Django administrative console

In order to access the administrative console at `/admin`, you need at least
one user account to be registered and configured as a super user or staff
account to access the Django administrative console.  This can be achieved by
doing the following:

    $ /opt/patchwork/manage.py createsuperuser

Once the administrative console is accessible, you would want to configure your
different sites and their corresponding domain names, which is required for the
different emails sent by patchwork (registration, password recovery) as well as
the sample `pwclientrc` files provided by your project's page.

## Incoming Email

Patchwork is designed to parse incoming mails which means you need an address
to receive email at. This is a problem that has been solved for many webapps,
thus there are many ways to go about this. Some of these ways are discussed
below.

### IMAP/POP3

The easiest option for getting mail into Patchwork is to use an existing email
address in combination with a mail retriever like [getmail][ref-getmail], which
will download mails from your inbox and pass them to Patchwork for processing.
getmail is easy to set up and configure: to begin, you need to install it:

    $ sudo apt-get install getmail4

Once installed, you should configure it, sustituting your own configuration
details where required below:

    $ sudo cat << EOF > /etc/getmail/user@example.com/getmailrc
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

Validate that this works as expected by starting `getmail`:

    $ getmail --getmaildir=/etc/getmail/user@example.com --idle INBOX

If everything works as expected, you can create a systemd script to ensure this
starts on boot:

    $ sudo cat << EOF > /etc/systemd/system/getmail.service
    [Unit]
    Description=Getmail for user@example.com

    [Service]
    User=pathwork
    ExecStart=/usr/bin/getmail --getmaildir=/etc/getmail/user@example.com --idle INBOX
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOF

And start the service:

    $ sudo systemctl start getmail
    $ sudo systemctl status getmail

### Mail Transfer Agent (MTA)

The most flexible option is to configure our own mail transfer agent (MTA) or
"email server". There are many options, of which [Postfix][ref-postfix] is one.
While we don't cover setting up Postfix here (it's complicated and there are
many guides already available), Patchwork does include a script to take
received mails and create the relevant entries in Patchwork for you. To use
this, you should configure your system to forward all emails to a given
localpart (the bit before the `@`) to this script. Using the `patchwork`
localpart (e.g. `patchwork@example.com`) you can do this like so:

    $ sudo cat << EOF > /etc/aliases
    patchwork: "|/opt/patchwork/patchwork/bin/parsemail.sh"
    EOF

You should ensure the appropriate user is created in PostgreSQL and that
it has (minimal) access to the database. Patchwork provides scripts for the
latter and they can be loaded as seen below:

    $ sudo -u postgres createuser nobody
    $ sudo -u postgre psql -f \
        /opt/patchwork/lib/sql/grant-all.postgres.sql patchwork

**NOTE:** This assumes your Postfix process is running as the `nobody` user.
If this is not correct (use of `postfix` user is also common), you should
change both the username in the `createuser` command above and substitute the
username in the `grant-all-postgres.sql` script with the appropriate
alternative.

### Use a Email-as-a-Service Provider

Setting up an email server can be a difficult task and, in the case of
deployment on PaaS provider, may not even be an option. In this case, there
are a variety of web services available that offer "Email-as-as-Service".
These services typically convert received emails into HTTP POST requests to
your endpoint of choice, allowing you to sidestep configuration issues. We
don't cover this here, but a simple wrapper script coupled with one of these
services can be more than to get email into Patchwork.

You can also create such as service yourself using a PaaS provider that
supports incoming mail and writing a little web app.

## (Optional) Configure your VCS to Automatically Update Patches

The `tools` directory of the Patchwork distribution contains a file named
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

[doc-contributing]: ../development/contributing.md
[doc-development]: development.md
[ref-django-files]: https://docs.djangoproject.com/en/dev/intro/tutorial01/#creating-a-project
[ref-django-settings]: https://docs.djangoproject.com/en/1.8/ref/settings/
[ref-getmail]: http://pyropus.ca/software/getmail/
[ref-pkgs]: http://pkgs.org/
[ref-postfix]: http://www.postfix.org/
[ref-uwsgi-emperor]: https://uwsgi-docs.readthedocs.io/en/latest/Emperor.html
[ref-uwsgi-systemd]: https://uwsgi-docs.readthedocs.io/en/latest/Systemd.html
[ref-uwsgi-upstart]: https://uwsgi-docs.readthedocs.io/en/latest/Upstart.html
