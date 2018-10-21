Design
======

**Patchwork should supplement mailing lists, not replace them**

Patchwork isn't intended to replace a community mailing list; that's why you
can't comment on a patch in Patchwork. If this were the case, then there would
be two forums of discussion on patches, which fragments the patch review
process. Developers who don't use Patchwork would get left out of the
discussion.

**Don't pollute the project's changelogs with Patchwork poop**

A project's changelogs are valuable - we don't want to add Patchwork-specific
metadata.

**Patchwork users shouldn't require a specific version control system**

Not everyone uses git for kernel development, and not everyone uses git for
Patchwork-tracked projects.

It's still possible to hook other programs into Patchwork, using various
:doc:`clients </usage/clients>` or the :doc:`APIs </api/index>` directly.
