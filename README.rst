=========
Patchwork
=========

.. image:: https://requires.io/github/getpatchwork/patchwork/requirements/?branch=master
   :target: https://requires.io/github/getpatchwork/patchwork/requirements.svg?branch=master
   :alt: Requirements Status

.. image:: https://codecov.io/gh/getpatchwork/patchwork/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/getpatchwork/patchwork
   :alt: Codecov

.. image:: https://landscape.io/github/getpatchwork/patchwork/master
   :target: https://landscape.io/github/getpatchwork/patchwork/master/landscape.svg?style=flat
   :alt: Code Health

.. image:: https://travis-ci.org/getpatchwork/patchwork
   :target: https://travis-ci.org/getpatchwork/patchwork.svg?branch=master
   :alt: Build Status

.. image:: https://readthedocs.org/projects/patchwork/badge/?version=latest
   :target: http://patchwork.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

**Patchwork** is a patch tracking system for community-based projects. It is
intended to make the patch management process easier for both the project's
contributors and maintainers, leaving time for the more important (and more
interesting) stuff.

Patches that have been sent to a mailing list are "caught" by the system, and
appear on a web page. Any comments posted that reference the patch are appended
to the patch page too. The project's maintainer can then scan through the list
of patches, marking each with a certain state, such as Accepted, Rejected or
Under Review. Old patches can be sent to the archive or deleted.

Currently, Patchwork is being used for a number of open-source projects, mostly
subsystems of the Linux kernel. Although Patchwork has been developed with the
kernel workflow in mind, the aim is to be flexible enough to suit the majority
of community projects.

Development Installation
------------------------

`Docker`_ is the recommended installation methods for a Patchwork
development environment. To install Patchwork:

1. Install **`Docker`_** and **`docker-compose`_**.

2. Clone the Patchwork repo::

       $ git clone https://github.com/getpatchwork/patchwork.git

3. Build the images. This will download over 200MB from the internet::

       $ docker-compose build

4. Run `docker-compose up`::

       $ docker-compose up

The Patchwork instance will now be deployed at `http://localhost:8000/`.

For more information, including helpful command line options and alternative
installation methods, refer to the `documentation`_.

Talks and Presentations
-----------------------

* **`Mailing List, Meet CI`_** - FOSDEM 2017

* **`Patches carved into stone tablets`_** - Kernel Recipes Conference 2016

* **`A New Patchwork`_** - FOSDEM 2016

* **`Patchwork: reducing your patch workload`_** - Linux Plumbers Conference
  2011

Additional Information
----------------------

For further information, refer to the `documentation`_.

Contact
-------

For bug reports, patch submissions or other questions, use the `mailing list`_.

.. _docker-compose: https://docs.docker.com/compose/install/
.. _Docker: https://docs.docker.com/engine/installation/linux/
.. _documentation: https://patchwork.readthedocs.io/
.. _mailing list: https://ozlabs.org/mailman/listinfo/patchwork
