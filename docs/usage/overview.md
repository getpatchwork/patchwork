# Overview

The key concepts or models of Patchwork are outlined below.

## Projects

Projects typically represent a software project or sub-project. A Patchwork
server can host multiple projects. Each project can have multiple maintainers.
Projects usually have a 1:1 mapping with a mailing list, though it's also
possible to have multiple projects in the same list using the subject as
filter. Patches, cover letters, and series are all associated with a single
project.

## People

People are anyone who has submitted a patch, cover letter, or comment to a
Patchwork instance.

## Users

Users are anyone who has created an account on a given Patchwork instance.

### Standard Users

A standard user can associate multiple email addresses with their user account,
create bundles and store TODO lists.

### Maintainers

Maintainers are a special type of user that with permissions to do certain
operations that regular Patchwork users can't. Patchwork maintainers usually
have a 1:1 mapping with a project's code maintainers though this is not
necessary.

The operations that a maintainer can invoke include:

- Change the state of a patch
- Archive a patch
- Delegate a patch, or be delegated a patch

## Submissions

Patchwork captures three types of mail to mailing lists: patches, cover
letters, and replies to either patches or cover letters, a.k.a. comments. Any
mail that does not fit one of these categories is ignored.

### Patches

Patches are the central object in Patchwork structure. A patch contains both a
diff and some metadata, such as the name, the description, the author, the
version of the patch etc. Patchwork stores not only the patch itself but also
various metadata associated with the email that the patch was parsed from, such
as the message headers or the date the message itself was received.

### Cover Letters

Cover letters provide a way to offer a "big picture" overview of a series of
patches. When using Git, these mails can be recognised by way of their `0/N`
subject prefix, e.g. `[00/11] A sample series`. Like patches, Patchwork stores
not only the various aspects of the cover letter itself, such as the name and
body of the cover letter, but also various metadata associated with the email
that the cover letter was parsed from.

### Comments

Comments are replies to a submission - either a patch or a cover letter. Unlike
a Mail User Agent (MUA) like Gmail, Patchwork does not thread comments.
Instead, every comment is associated with either a patch or a cover letter, and
organized by date.

## Patch Metadata

Patchwork allows users to store various metadata against patches. This metadata
is only configurable by a maintainer.

### States

States track the state of patch in its lifecycle. States vary from project to
project, but generally a minimum subset of "new", "rejected" and "accepted"
will exist.

### Delegates

Delegates are Patchwork users who are responsible for both reviewing a patch
and setting its eventual state in Patchwork. This makes them akin to reviewers
in other tools. Delegation works particularly well for larger projects where
various subsystems, each with their own maintainer(s), can be identified. Only
one delegate can be assigned to a patch.

**NOTE:** Patchwork supports automatic delegation of patches. Refer to the
[Autodelegation Guide][doc-autodelegation] for more information.

### Tags

Tags are specially formatted metadata appended to the foot the body of a patch
or a comment on a patch. Patchwork extracts these tags at parse time and
associates them with the patch. You add extra tags to an email by replying to
the email. The following tags are available on a standard Patchwork install:

- Acked-by:

    For example:

        Acked-by: Stephen Finucane <stephen@that.guru>

- Tested-by:

    For example:

        Tested-by: Stephen Finucane <stephen@that.guru>

- Reviewed-by:

    For example:

        Tested-by: Stephen Finucane <stephen@that.guru>

The available tags, along with the significance of said tags, varies from
project to project and Patchwork instance to Patchwork instance. The [kernel
project documentation][ref-kernel-submission] provides an overview of the
supported tags for the Linux kernel project.

### Checks

Checks store the results of any tests executed (or executing) for a given
patch. This is useful, for example, when using a continuous integration (CI)
system to test patches. Checks have a number of fields associated with them:

- Context

    A label to discern check from the checks of other testing systems

- Description

    A brief, optional description of the check

- Target URL

    A target URL where a user can find information related to this check, such
    as test logs.

- State

    The state of the check. One of: pending, success, warning, fail

- User

    The user creating the check

**NOTE:** Checks can only be created through the Patchwork APIs. Refer to the
[API documentation][doc-api] for more information.

**TODO:** Provide information on building a CI system that reports check
results back to Patchwork.

## Collections

Patchwork provides a number of ways to store groups of patches. Some of these
are automatically generated, while others are user-defined.

### Series

Series are groups of patches, along with an optional cover letter. Series are
mostly dumb containers, though they also contain some metadata themselves such
as a version (which is inherited by the patches and cover letter) and a count
of the number of patches found in the series.

### Bundles

Bundles are custom, user-defined groups of patches. Bundles can be used to keep
patch lists, preserving order, for future inclusion in a tree. There's no
restriction of number of patches and they don't even need to be in the same
project. A single patch also can be part of multiple bundles at the same time.
An example of Bundle usage would be keeping track of the Patches that are ready
for merge to the tree.

### To-do Lists

Patchwork users can store a to-do list of patches.

[doc-api]: rest.md
[doc-autodelegation]: delegation.md
[ref-kernel-submission]: https://www.kernel.org/doc/Documentation/SubmittingPatches
