Release Process
===============

Versioning
----------

There are two types of versioning in play in Patchwork: the version for
Patchwork itself (i.e. the code or *core*) and the version for the `REST
API <../api/rest>`.

Patchwork Code
~~~~~~~~~~~~~~

Since version 1.0, Patchwork has implemented a version of `Semantic
Versioning`__ . To summarise, releases take the format **MAJOR.MINOR.PATCH**
(or just **MAJOR.MINOR**). We increment:

1. **MAJOR** version when we make major UI changes or functionality updates

2. **MINOR** version when we make minor UI changes or functionality updates

3. **PATCH** version when we make make bug fixes, dependency updates etc.

In Git, each release will have a tag indicating the version number. In
addition, each release series has it's own branch called `stable/MAJOR.MINOR`
to allow backporting of bugfixes or security updates to older versions.

__ http://semver.org/

REST API
~~~~~~~~

The REST API also uses a variant of *Semantic Versioning*. To summarise, API
versions take the format **MAJOR.MINOR**. We increment:

1. **MAJOR** version when we make breaking changes to the API. This generally
   means removing an API or fields in an API.

2. **MINOR** version when we add functionality in a backwards-compatible
   manner. This generally means adding new fields and endpoint.

These version numbers are exposed via the API and it's possible to request a
specific version in the URL. Refer to the `API Guide <../api/rest>` for more
information.


Release Cycle
-------------

There is no cadence for releases: they are made available as necessary.


Supported Versions
------------------

Typically all development should occur on ``master``. While we will backport
bugfixes and security updates, we will not backport any new features. This is
to ensure stability for users of these versions of Patchwork.


Release Checklist
-----------------

The follow steps apply to all releases:

* Documentation has been updated with latest release version

* Documentation references latest supported version of Django

* 'alpha' tag has been removed from ``__version__`` in
  ``patchwork/__init__.py``

* Commit has been tagged with an `annotated tag`__. The tag should take the
  form `v[MAJOR].[MINOR].[PATCH]`, e.g. `v2.0.1`. The message should read::

    Version [MAJOR].[MINOR].[PATCH]

* A `GitHub Release`__, with text corresponding to an abbreviated form of the
  release notes for that cycle, has been created

* An email describing the release and top-level overview of the changes has
  been sent to the mailing list. Refer to the emails for `Patchwork v2.0.0`__
  and `Patchwork v2.0.1`__ for examples.

The following only apply to full releases, or those where the **MAJOR** or
**MINOR** number is incremented:

* A new branch called ``stable/MAJOR.MINOR`` has been created from the tagged
  commit

Once released, bump the version found in ``patchwork/__init__.py`` once again.

__ https://git-scm.com/book/en/v2/Git-Basics-Tagging
__ https://github.com/getpatchwork/patchwork/releases/new
__ https://lists.ozlabs.org/pipermail/patchwork/2017-August/004549.html
__ https://lists.ozlabs.org/pipermail/patchwork/2017-December/004683.html


Backporting
-----------

We will occasionally backport bugfixes and security updates. When backporting a
patch, said patch should first be merged into ``master``. Once merged, you can
backport by cherry-picking commits, using the ``-x`` flag for posterity:

.. code-block:: shell

   $ git cherry-pick -x <master_commit>

There may be some conflicts; resolve these, uncommenting the `Conflicts` line
when committing::

   Conflicts
           patchwork/bin/pwclient

When enough patches have been backported, you should release a new **PATCH**
release.
