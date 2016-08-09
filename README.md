# Patchwork

[![Requirements Status][badge-req-img]][badge-req-ref]
[![Docs Status][badge-doc-img]][badge-doc-ref]
[![Stories in Ready][badge-waffle-img]][badge-waffle-ref]

**Patchwork** is a patch tracking system for community-based projects. It is
intended to make the patch management process easier for both the project's
contributors and maintainers, leaving time for the more important (and more
interesting) stuff.

Patches that have been sent to a mailing list are 'caught' by the system, and
appear on a web page. Any comments posted that reference the patch are appended
to the patch page too. The project's maintainer can then scan through the list
of patches, marking each with a certain state, such as Accepted, Rejected or
Under Review. Old patches can be sent to the archive or deleted.

Currently, Patchwork is being used for a number of open-source projects, mostly
subsystems of the Linux kernel. Although Patchwork has been developed with the
kernel workflow in mind, the aim is to be flexible enough to suit the majority
of community projects.

# Development Installation using Vagrant

1. Install [**Vagrant**][ref-vagrant]
2. Clone this repo:

        $ git clone git://github.com/getpatchwork/patchwork.git

3. Run `vagrant up`:

        $ cd patchwork
        $ vagrant up

# Development Installation using Docker

1. Install Docker and docker-compose.
2. Clone this repo, as with vagrant.
3. Build the images. This will download over 200MB from the internet:

        $ docker-compose build

4. Run as follows:

  * Regular server:

          $ docker-compose up

    This will be visible on http://localhost:8000/.

  * Shell:

          $ docker-compose run --rm web --shell

  * Quick test (not including selenium UI interaction tests):

          $ docker-compose run --rm web --quick-test

  * Full tests, including selenium, run headlessly:

          $ docker-compose run --rm web --test

  * To reset the database before beginning, add `--reset` to the command line after `web` and before any other arguments.

  * If you want to run non-headless tests, you'll need something like this ugly hack:

          $ docker run -it --rm -v (pwd):/home/patchwork/patchwork/ --link patchwork_db_1:db -p 8000:8000 -v /tmp/.X11-unix:/tmp/.X11-unix -e PW_TEST_DB_HOST=db -e DISPLAY patchwork_web bash

With both vagrant and docker, any edits to the project files made locally are immediately visible to the VM/container, and so should be picked up by the Django auto-reloader.

# Talks and Presentations

* [**A New Patchwork**][pdf-fosdem] - FOSDEM 2016
* [**Patchwork: reducing your patch workload**][pdf-plumbers] - Linux Plumbers
  Conference 2011

# Additional Information

For further information, please refer to the [docs][docs].

# Contact

For bug reports, patch submissions or other questions, please use the
[Patchwork mailing list][pw-ml].

[badge-doc-ref]: https://patchwork.readthedocs.org/en/latest/
[badge-doc-img]: https://readthedocs.org/projects/patchwork/badge/?version=latest
[badge-req-ref]: https://requires.io/github/getpatchwork/patchwork/requirements/?branch=master
[badge-req-img]: https://requires.io/github/getpatchwork/patchwork/requirements.svg?branch=master
[badge-waffle-ref]: https://waffle.io/getpatchwork/patchwork
[badge-waffle-img]: https://badge.waffle.io/getpatchwork/patchwork.svg?label=ready&title=Ready
[docs]: https://patchwork.readthedocs.org/en/latest/
[pdf-fosdem]: https://speakerdeck.com/stephenfin/a-new-patchwork-bringing-ci-patch-tracking-and-more-to-the-mailing-list
[pdf-plumbers]: https://www.linuxplumbersconf.org/2011/ocw/system/presentations/255/original/patchwork.pdf
[pw-ml]: https://ozlabs.org/mailman/listinfo/patchwork
[ref-vagrant]: https://www.vagrantup.com/docs/getting-started/
