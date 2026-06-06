v2.0 Series ("Dazzle")
======================

.. _Release Notes_v2.0.3_stable_2.0:

v2.0.3
======

.. _Release Notes_v2.0.3_stable_2.0_Bug Fixes:

Bug Fixes
---------

- If a patch was processed by Patchwork before series support was added, it
  will not have a series associated with it. As a result, it is not possible
  to extract the dependencies for that patch from the series. This was not
  previously handled correctly. A 404 is now raised if this occurs.

- The ``parsemail.sh`` and ``parsemail-batch.sh`` scripts, found in
  ``patchwork/bin``, will now default to using ``python`` rather than
  ``python2`` for calling ``manage.py``. This resolves an issue when
  Patchwork is deployed with a virtualenv.


.. _Release Notes_v2.0.2_stable_2.0:

v2.0.2
======

.. _Release Notes_v2.0.2_stable_2.0_Bug Fixes:

Bug Fixes
---------

- Resolve some issues caused by parallel parsing of series.

- Poorly formatted email headers are now handled correctly.

- Patches with CRLF newlines are now parsed correctly and these line endings
  are stripped when saving patches.

- Resolved some issues with pagination.

- Emails from *git-pull-request* v2.14.3+ are now handled correctly.

- Token generation from the web UI is now disabled if the REST API is
  disabled. This was causing an exception.

- Non-breaking spaces in tags are now handled correctly.

- Patches with no space before the series marker, such as ``PATCH1/8``, are
  now parsed correctly.


.. _Release Notes_v2.0.1_stable_2.0:

v2.0.1
======

.. _Release Notes_v2.0.1_stable_2.0_Bug Fixes:

Bug Fixes
---------

- Handle requests for pages out of range.

- Fix SQL permissions scripts for tables and columns added in 2.0.

- Fix filtering of projects by name

- Fix "add to bundle" dropdown

- Performance improvements for the XML-RPC API


.. _Release Notes_v2.0.0_stable_2.0:

v2.0.0
======

.. _Release Notes_v2.0.0_stable_2.0_Prelude:

Prelude
-------

The v2.0.0 release includes many new features and bug fixes. For full
information on the options avaiable, you should look at the full release
notes in detail. However, there are two key features that make v2.0.0 a
worthwhile upgrade:

- A REST API is now provided, which will eventually replace the legacy
  XML-RPC API
- Patch series and series cover letters are now supported

For further information on these features and the other changes in this
release, review the full release notes.


.. _Release Notes_v2.0.0_stable_2.0_New Features:

New Features
------------

- REST API.

  Previous versions of Patchwork provided an XML-RPC API. This was functional
  but there were a couple of issues around usability and general design. This
  API also provided basic versioning information but the existing clients,
  mostly `pwclient` variants, did not validate this version. Together, this
  left us with an API that needed work but no way to fix it without breaking
  every client out there.

  Rather than breaking all those users, make a clean break and provide
  another API method. REST APIs are the API method de jour providing a number
  of advantages over XML-RPC APIs, thus, a REST API is chosen. The following
  resources are exposed over this new API:

  - Bundles
  - Checks
  - Projects
  - People
  - Users
  - Patches
  - Series
  - Cover letters

  For information on the usage of the API, refer to the `documentation
  <https://patchwork.readthedocs.io/en/latest/api/rest/>`__.

- Cover letters are now supported.

  Cover letters are often sent in addition to a series of patches. They do
  not contain a diff and can generally be identified as number 0 of a series.
  For example::

    [PATCH 0/3] A cover letter

  Cover letters contain useful information that should not be discarded.
  Both cover letters and replies to these mails are now stored for use with
  series.

- Series are now supported.

  Series are groups of patches sent as one bundle. For example::

    [PATCH 0/3] A cover letter
      [PATCH 1/3] The first patch
      [PATCH 2/3] The second patch
      [PATCH 3/3] The third patch

  While Patchwork already supports bundles, these must be created manually,
  defeating the purpose of using series in the first place. Series make use
  of the information provided in the emails themselves, avoiding this manual
  step. The series support implemented is basic and does not support
  versioning. This will be added in a future release.

- All comments now have a permalink which can be used to reference individual
  replies to patches and cover letters.

- `Django Debug Toolbar <https://pypi.python.org/pypi/django-debug-toolbar>`_
  is now enabled by defaut when using development settings.

- `Django 1.9 <https://docs.djangoproject.com/en/1.10/releases/1.9/>`_ and
  `1.10 <https://docs.djangoproject.com/en/1.10/releases/1.10/>`_ are now
  supported.

- `Python 3.5 <https://www.python.org/downloads/release/python-350/>`_ is now
  supported.

- `Docker <https://www.docker.com/what-docker#/developers>`_ support is now
  integrated for development usage. To use this, refer to the `documentation
  <https://patchwork.readthedocs.io/en/latest/development/installation/>`__.

- Series markers are now parsed from patches generated by the `Mercurial
  Patchbomb extension
  <https://www.mercurial-scm.org/wiki/PatchbombExtension>`__.


.. _Release Notes_v2.0.0_stable_2.0_Upgrade Notes:

Upgrade Notes
-------------

- The REST API is enabled by default.

  The REST API is enabled by default. It is possible to disable this API,
  though this functionality may be removed in a future release. Should you
  wish to disable this feature, configure the ``ENABLE_REST_API`` setting to
  ``False``.

- The ``parsemail.py`` and ``parsearchive.py`` scripts have been replaced by
  the ``parsemail`` and ``parsearchive`` management commands. These can be
  called like any other management commands. For example::

    $ ./manage.py parsemail [args...]

- The ``DEFAULT_PATCHES_PER_PAGE`` has been renamed as
  ``DEFAULT_ITEMS_PER_PAGE`` as it is now possible to list cover letters in
  addition to patches.

- The ``context`` field for patch checks must now be slug, or a string
  consisting of only ASCII letters, numbers, underscores or hyphens. While
  older, non-slugified strings won't cause issues, any scripts creating
  contexts must be updated where necessary.


.. _Release Notes_v2.0.0_stable_2.0_Bug Fixes:

Bug Fixes
---------

- When downloading an mbox, a user's name will now be set to the name used in
  the last email recieved from them. Previously, the name used in the first
  email received from a user was used.

- `user at domain`-style email addresses, commonly found in Mailman archives,
  are now handled correctly.

- Unicode characters transmitted over the XML-RPC API are now handled
  correctly under Python 3

- The `pwclient` tool will no longer attempt to re-encode unicode to ascii
  bytes, which was a frequent cause of ``UnicodeEncodeError`` exceptions.
  Instead, a warning is produced if your environement is not configured for
  unicode.


.. _Release Notes_v2.0.0_stable_2.0_Other Notes:

Other Notes
-----------

- `reno <https://pypi.python.org/pypi/reno>`_ is now used for release note
  management.

- Patch diffs now download with a ``diff`` extension.
