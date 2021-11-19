=========
Patchwork
=========

.. image:: https://pyup.io/repos/github/getpatchwork/patchwork/shield.svg
   :target: https://pyup.io/repos/github/getpatchwork/patchwork/
   :alt: Requirements Status

.. image:: https://codecov.io/gh/getpatchwork/patchwork/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/getpatchwork/patchwork
   :alt: Codecov

.. image:: https://github.com/getpatchwork/patchwork/actions/workflows/ci.yaml/badge.svg
   :target: https://github.com/getpatchwork/patchwork/actions/workflows/ci.yaml
   :alt: Build Status

.. image:: https://readthedocs.org/projects/patchwork/badge/?version=latest
   :target: http://patchwork.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/discord/857116373653127208.svg?label=&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2
   :target: https://discord.gg/hGWjXVTAbB
   :alt: Discord

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

Patchwork requires reasonably recent versions of:

- Python 3

- Django

- Django REST Framework

- Django Filters

The precise versions supported are listed in the `release notes`_.

Development Installation
------------------------

`Docker`_ is the recommended installation method for a Patchwork development
environment. To install Patchwork:

1. Install `Docker`_ and `docker-compose`_.

2. Clone the Patchwork repo::

       $ git clone https://github.com/getpatchwork/patchwork.git

3. Create a ``.env`` file in the root directory of the project and store your
   ``UID`` and ``GID`` attributes there::

       $ cd patchwork && printf "UID=$(id -u)\nGID=$(id -g)\n" > .env

4. Build the images. This will download a number of packages from the internet,
   and compile several versions of Python::

       $ docker-compose build

5. Run `docker-compose up`::

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

.. _release notes: https://patchwork.readthedocs.io/en/latest/releases/
.. _docker-compose: https://docs.docker.com/compose/install/
.. _Docker: https://docs.docker.com/engine/installation/linux/
.. _documentation: https://patchwork.readthedocs.io/
.. _mailing list: https://ozlabs.org/mailman/listinfo/patchwork
