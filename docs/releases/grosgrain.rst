v3.0 Series ("Grosgrain")
=========================

.. _Release Notes_v3.0.5_stable_3.0:

v3.0.5
======

.. _Release Notes_v3.0.5_stable_3.0_Bug Fixes:

Bug Fixes
---------

- Comments and whitespace are now correctly stripped from the ``Message-ID``,
  ``In-Reply-To``, and ``References`` headers. One side effect of this change
  is that the parser is now stricter with regards to the format of the
  ``msg-id`` component of these headers: all identifiers must now be
  surrounded by angle brackets, e.g. ``<abcdef@example.com>``. This is
  mandated in the spec and a review of mailing lists archives suggest it is
  broadly adhered to. Without these markers, there is no way to delimit
  ``msg-id`` from any surrounding comments and whitespace.


.. _Release Notes_v3.0.1_stable_3.0:

v3.0.1
======

.. _Release Notes_v3.0.1_stable_3.0_Bug Fixes:

Bug Fixes
---------

- Fixed a compatability issue with Django 3.1 that prevented users from
  resetting their password.
  (`#394 <https://github.com/getpatchwork/patchwork/issues/394>`__)


.. _Release Notes_v3.0.1_stable_3.0_API Changes:

API Changes
-----------

- The ``list_archive_url`` field will now be correctly shown for patch
  comments and cover letter comments.
  (`#391 <https://github.com/getpatchwork/patchwork/issues/391>`__)


.. _Release Notes_v3.0.0_stable_3.0:

v3.0.0
======

.. _Release Notes_v3.0.0_stable_3.0_Prelude:

Prelude
-------

There are two main changes in this release: the removal of Python 2.7 support
and the resolution of the longstanding performance issues introduced by the
``Submission`` model. On top of this, there is the usual bump in
requirements, a significant amount of fixes to the documentation for the
REST API, and the squashing of all migrations introduced in versions up to
and including v2.2.0.


.. _Release Notes_v3.0.0_stable_3.0_New Features:

New Features
------------

- `Django 3.0 <https://docs.djangoproject.com/en/dev/releases/3.0/>`_ is
  now supported.

- `Django 3.1 <https://docs.djangoproject.com/en/dev/releases/3.1/>`_ is
  now supported.

- `Django REST Framework 3.12
  <https://www.django-rest-framework.org/community/3.12-announcement/>`_ is
  now supported.

- `Python 3.9 <https://www.python.org/downloads/release/python-390/>`_ is now
  supported.


.. _Release Notes_v3.0.0_stable_3.0_Upgrade Notes:

Upgrade Notes
-------------

- Django 1.11, 2.0 and 2.1 are no longer supported. These are no longer
  supported upstream and most distributions provide a newer version.

- djangorestframework 3.6, 3.7, 3.8 and 3.9 are no longer supported. These
  were only used with Django 1.11 to 2.1 and are not compatible with any
  version now supported by Patchwork.

- django-filter 1.1.0 is no longer supported. This was only used with Django
  1.11 and is not compatible with any version now supported by Patchwork.

- Python 2.7 and 3.5 are no longer supported. These are no longer supported
  upstream and most distributions provide a newer version.


.. _Release Notes_v3.0.0_stable_3.0_Bug Fixes:

Bug Fixes
---------

- An issue that preventing updating bundles via the REST API without
  updating the included patches has been resolved.
  (`#357 <https://github.com/getpatchwork/patchwork/issues/357>`__)

- The parser module now uses an atomic select-insert when creating new patch,
  cover letter and comment entries. This prevents the integrity errors from
  being logged in the DB logs.
  (`#358 <https://github.com/getpatchwork/patchwork/issues/358>`__)

- Resolve a bug that would prevent listing patches for a project via the
  browseable API view when logged in with admin permissions (`issue #379`__)

  __ https://github.com/getpatchwork/patchwork/issues/379

- Previously, it was possible to create a project with a ``linkname``
  containing invalid URL characters. This would result in broken URLs. We
  now validate this field and restrict characters to unicode slugs (unicode
  letters, numbers, underscores and hyphens).


.. _Release Notes_v3.0.0_stable_3.0_API Changes:

API Changes
-----------

- The REST API now supports filtering patches and cover letters by message
  ID, using the ``msgid`` query parameter. Don't include leading or trailing
  angle brackets.
