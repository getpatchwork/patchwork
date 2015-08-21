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

       (django-1.8)$ pip install -r docs/requirements-dev.txt

   You will also need to install a version of Django - we don't install this
   by default to allow development against multiple versions of Django. This
   can be installed like so (assuming Django 1.8):

       (django-1.8)$ pip install 'django<1.9,>=1.8'

   Of course, this is a one-time step: once installed in the virtual
   environment there is no need to to install requirements again.

5. Run the development server

       (django-1.8)$ ./manage.py --version
       1.8
       (django-1.8)$ ./manage.py runserver

Once finished, you can kill the server (`Ctrl` + `C`) and exit the the virtual
environment:

    (django-1.8)$ deactivate
    $

Should you wish to re-enter this environment, simply source the `activate`
script again.

## Running Tests

patchwork includes a [tox] script to automate testing. Before running this, you
should probably install tox:

    $ pip install tox

You can show available
targets like so:

    $ tox --list

You'll see that this includes a number of targets to run unit tests against the
different versions of Django supported, along with some other targets related
to code coverage and code quality. To run these, use the `-e` parameter:

    $ tox -e py27-django18

In the case of the unit tests targets, you can also run specific tests by
passing the fully qualified test name as an additional argument to this
command:

    $ tox -e py27-django18 patchwork.tests.SubjectCleanUpTest

Because patchwork support multiple versions of Django, it's very important
that you test against all supported versions. When run without argument, tox
will do this:

    $ tox

[tox]: https://tox.readthedocs.org/en/latest/
