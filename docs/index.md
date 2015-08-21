# patchwork

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

# Download

The latest version of Patchwork is available with git. To download:

    $ git clone git://ozlabs.org/home/jk/git/patchwork

Patchwork is distributed under the [GNU General Public License].

# Design

## patchwork should supplement mailing lists, not replace them

Patchwork isn't intended to replace a community mailing list; that's why you
can't comment on a patch in patchwork. If this were the case, then there would
be two forums of discussion on patches, which fragments the patch review
process. Developers who don't use patchwork would get left out of the
discussion.

However, a future development item for patchwork is to facilitate on-list
commenting, by providing a "send a reply to the list" feature for logged-in
users.

## Don't pollute the project's changelogs with patchwork poop

A project's changelogs are valuable - we don't want to add patchwork-specific
metadata.

## patchwork users shouldn't require a specific version control system

Not everyone uses git for kernel development, and not everyone uses git for
patchwork-tracked projects.

It's still possible to hook other programs into patchwork, using the pwclient
command-line client for patchwork, or directly to the XML RPC interface.

# Getting Started

You should check out the [installation] and [development] guides for
information on how to get to work with patchwork.

# Support

All questions and contributions should be sent to the [patchwork mailing list].

[GNU General Public License]: http://www.gnu.org/licenses/gpl-2.0.html
[installation]: installation.md
[development]: development.md
[patchwork mailing list]: https://ozlabs.org/mailman/listinfo/patchwork
