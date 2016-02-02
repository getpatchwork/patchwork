# Developing patchwork

## Using virtualenv

It's a good idea to use virtualenv to develop Python software. Virtual
environments are "instances" of your system Python, without any of the
additional Python packages installed. They are useful to develop and deploy
patchwork against a "well known" set of dependencies, but they can also be
used to test patchwork against several versions of Django.

1. Install pip, virtualenv (python-pip, python-virtualenv packages)

   Because we're going to recompile our dependencies, we'll also need
   development headers. For the MySQL/MariaDB setups these are
   `mariadb-devel` (Fedora), `libmysqlclient-dev` (Debian)

2. Create a new virtual environement.

   Inside a virtual env, we'll just install the dependencies needed for
   patchwork and run it from there.

        $ virtualenv django-1.8

   This will create a virtual env called 'django-1.8' in eponymous directory.

3. Activate a virtual environment

        $ source django-1.8/bin/activate
        (django-1.8)$

   The shell prompt is preprended with the virtual env name.

4. Install the required dependencies

   To ease this task, it's customary to maintain a list of dependencies in a
   text file and install them in one go. One can maintain such a list of
   dependencies per interesting configuration.

        (django-1.8)$ pip install -r requirements-dev.txt

   You will also need to install a version of Django - we don't install this
   by default to allow development against multiple versions of Django. This
   can be installed like so (assuming Django 1.8):

        (django-1.8)$ pip install 'django<1.9,>=1.8'

   Of course, this is a one-time step: once installed in the virtual
   environment there is no need to to install requirements again.

5. Export the `DJANGO_SETTINGS_MODULE` path

   If you are using the provided `settings/dev.py` file, you can simply export
   the path to this (in Python module format) like so:

        (django-1.8)$ export DJANGO_SETTINGS_MODULE=patchwork.settings.dev

   If you do so, you may also need to configure you database configuration.
   See the [Environmental Configuration](#environmental-configuration) section
   below for details on the specific variables to export. For example:

        (django-1.8)$ export PW_TEST_DB_USER=root

   You can also provide your own `settings.py` file. Simply change the path
   used for `DJANGO_SETTINGS_MODULE` above and omit the `PW_` related steps.

6. Run the development server

        (django-1.8)$ ./manage.py runserver

Once finished, you can kill the server (`Ctrl` + `C`) and exit the virtual
environment:

    (django-1.8)$ deactivate
    $

Should you wish to re-enter this environment, simply source the `activate`
script again.

## Environmental Variables

The following environmental variables are available to configure settings:

<dl>
  <dt>PW_TEST_DB_NAME = 'patchwork'</dt>
  <dd>Name of the database</dd>
  <dt>PW_TEST_DB_USER = 'patchwork'</dt>
  <dd>Username to access the database with</dd>
  <dt>PW_TEST_DB_PASS = 'password'</dt>
  <dd>Password to access the database with</dd>
  <dt>PW_TEST_DB_TYPE = 'mysql'</dt>
  <dd>Type of database to use. Options: 'mysql', 'postgresql'</dd>
</dl>
