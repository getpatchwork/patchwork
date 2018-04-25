=========
Patchwork
=========

.. image:: https://requires.io/github/getpatchwork/patchwork/requirements.svg?branch=master
   :target: https://requires.io/github/getpatchwork/patchwork/requirements/?branch=master
   :alt: Requirements Status

.. image:: https://codecov.io/gh/getpatchwork/patchwork/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/getpatchwork/patchwork
   :alt: Codecov

.. image:: https://landscape.io/github/getpatchwork/patchwork/master/landscape.svg?style=flat
   :target: https://landscape.io/github/getpatchwork/patchwork/master
   :alt: Code Health

.. image:: https://travis-ci.org/getpatchwork/patchwork.svg?branch=master
   :target: https://travis-ci.org/getpatchwork/patchwork
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

Requirements
------------

- Python (2.7, 3.4 - 3.6)

- Django (1.8 - 1.11)

- Django REST Framework (3.2 - 3.6)

- Django Filters (1.0)

Development Installation
------------------------

`Docker`_ is the recommended installation methods for a Patchwork development
environment. To install Patchwork:

1. Install `Docker`_ and `docker-compose`_.

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

* **Mailing List, Meet CI** (slides__) - FOSDEM 2017

* **Patches carved into stone tablets** (slides__) - Kernel Recipes Conference
  2016

* **A New Patchwork** (slides__) - FOSDEM 2016

* **Patchwork: reducing your patch workload** (slides__) - Linux Plumbers
  Conference 2011

__ https://speakerdeck.com/stephenfin/mailing-list-meet-ci
__ https://github.com/gregkh/presentation-stone-tools/blob/34a3963/stone-tools.pdf
__ https://speakerdeck.com/stephenfin/a-new-patchwork-bringing-ci-patch-tracking-and-more-to-the-mailing-list
__ https://www.linuxplumbersconf.org/2011/ocw/system/presentations/255/original/patchwork.pdf

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
