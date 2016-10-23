# Patchwork

[![Requirements Status][badge-req-img]][badge-req-ref]
[![Build Status][badge-travis-img]][badge-travis-ref]
[![Code Health][badge-landscape-img]][badge-landscape-ref]
[![Codecov][badge-codecov-img]][badge-codecov-ref]
[![Docs Status][badge-doc-img]][badge-doc-ref]
[![Stories in Ready][badge-waffle-img]][badge-waffle-ref]

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

# Development Installation

[Docker][ref-docker] is the recommended installation methods for a Patchwork
development environment. To install Patchwork:

1. Install [**Docker**][ref-docker] and [**docker-compose**][ref-compose].
2. Clone the Patchwork repo:

        $ git clone https://github.com/getpatchwork/patchwork.git

3. Build the images. This will download over 200MB from the internet:

        $ docker-compose build

4. Run `docker-compose up`:

        $ docker-compose up

The Patchwork instance will now be deployed at `http://localhost:8000/`.

For more information, including helpful command line options and alternative
installation methods, refer to the [development installation
guide][docs-development].

# Talks and Presentations

* [**A New Patchwork**][pdf-fosdem] - FOSDEM 2016
* [**Patches carved into stone tablets**][pdf-stone-tools] - Kernel Recipes
  Conference 2016
* [**Patchwork: reducing your patch workload**][pdf-plumbers] - Linux Plumbers
  Conference 2011

# Additional Information

For further information, please refer to the [docs][docs].

# Contact

For bug reports, patch submissions or other questions, please use the
[Patchwork mailing list][pw-ml].

[badge-codecov-ref]: https://codecov.io/gh/getpatchwork/patchwork
[badge-codecov-img]: https://codecov.io/gh/getpatchwork/patchwork/branch/master/graph/badge.svg
[badge-doc-ref]: https://patchwork.readthedocs.io/en/latest/
[badge-doc-img]: https://readthedocs.org/projects/patchwork/badge/?version=latest
[badge-landscape-ref]: https://landscape.io/github/getpatchwork/patchwork/master
[badge-landscape-img]: https://landscape.io/github/getpatchwork/patchwork/master/landscape.svg?style=flat
[badge-req-ref]: https://requires.io/github/getpatchwork/patchwork/requirements/?branch=master
[badge-req-img]: https://requires.io/github/getpatchwork/patchwork/requirements.svg?branch=master
[badge-travis-ref]: https://travis-ci.org/getpatchwork/patchwork
[badge-travis-img]: https://travis-ci.org/getpatchwork/patchwork.svg?branch=master
[badge-waffle-ref]: https://waffle.io/getpatchwork/patchwork
[badge-waffle-img]: https://badge.waffle.io/getpatchwork/patchwork.svg?label=ready&title=Ready
[docs]: https://patchwork.readthedocs.io/en/latest/
[docs-development]: https://patchwork.readthedocs.io/en/latest/development/
[pdf-fosdem]: https://speakerdeck.com/stephenfin/a-new-patchwork-bringing-ci-patch-tracking-and-more-to-the-mailing-list
[pdf-plumbers]: https://www.linuxplumbersconf.org/2011/ocw/system/presentations/255/original/patchwork.pdf
[pdf-stone-tools]: https://github.com/gregkh/presentation-stone-tools/blob/34a3963/stone-tools.pdf
[pw-ml]: https://ozlabs.org/mailman/listinfo/patchwork
[ref-compose]: https://docs.docker.com/compose/install/
[ref-docker]: https://docs.docker.com/engine/installation/linux/
