# patchwork

[![Requirements Status][badge-req-img]][badge-req-ref]
[![Docs Status][badge-doc-img]][badge-doc-ref]
[![Stories in Ready][badge-waffle-img]][badge-waffle-ref]

patchwork is a patch tracking system for community-based projects. It is
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

# Additional Information

For further information, please refer to the [docs][docs].

[docs]: https://patchwork.readthedocs.org/en/latest/
[badge-doc-ref]: https://patchwork.readthedocs.org/en/latest/
[badge-doc-img]: https://readthedocs.org/projects/patchwork/badge/?version=latest
[badge-req-ref]: https://requires.io/github/getpatchwork/patchwork/requirements/?branch=master
[badge-req-img]: https://requires.io/github/getpatchwork/patchwork/requirements.svg?branch=master
[badge-waffle-ref]: https://waffle.io/getpatchwork/patchwork
[badge-waffle-img]: https://badge.waffle.io/getpatchwork/patchwork.svg?label=ready&title=Ready
