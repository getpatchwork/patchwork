# patchwork

[![Requirements Status][badge-req-img]][badge-req-ref]
[![Docs Status][badge-doc-img]][badge-doc-ref]
[![Stories in Ready][badge-waffle-img]][badge-waffle-ref]

**patchwork** is a patch tracking system for community-based projects. It is
intended to make the patch management process easier for both the project's
contributors and maintainers, leaving time for the more important (and more
interesting) stuff.

Patches that have been sent to a mailing list are 'caught' by the system, and
appear on a web page. Any comments posted that reference the patch are appended
to the patch page too. The project's maintainer can then scan through the list
of patches, marking each with a certain state, such as Accepted, Rejected or
Under Review. Old patches can be sent to the archive or deleted.

Currently, patchwork is being used for a number of open-source projects, mostly
subsystems of the Linux kernel. Although Patchwork has been developed with the
kernel workflow in mind, the aim is to be flexible enough to suit the majority
of community projects.

# Development Installation

1. Install [**Vagrant**][ref-vagrant]
2. Clone this repo:

        $ git clone git://github.com/getpatchwork/patchwork.git

3. Run `vagrant up`:

        $ cd patchwork
        $ vagrant up

# Talks and Presentations

* [**A New Patchwork**][pdf-fosdem] - FOSDEM 2016
* [**Patchwork: reducing your patch workload**][pdf-plumbers] - Linux Plumbers
  Conference 2011

# Additional Information

For further information, please refer to the [docs][docs].

# Contact

For bug reports, patch submissions or other questions, please use the
[patchwork mailing list][pw-ml].

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
