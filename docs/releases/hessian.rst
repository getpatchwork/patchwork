v3.1 Series ("Hessian")
=======================

.. _Release Notes_v3.1.1_stable_3.1:

v3.1.1
======

.. _Release Notes_v3.1.1_stable_3.1_New Features:

New Features
------------

- The version of Django used is now checked on start-up. This can help avoid
  issues where deployers forget to update their Django version and see odd
  behavior as a result.


.. _Release Notes_v3.1.1_stable_3.1_Bug Fixes:

Bug Fixes
---------

- Fix an issue whereby comment-based events would cause a HTTP 500 error
  for the events API (``/api/events``).


.. _Release Notes_v3.1.0_stable_3.1:

v3.1.0
======

.. _Release Notes_v3.1.0_stable_3.1_Prelude:

Prelude
-------

This release is one of the smaller releases. The primary new feature is the ability to mark comments as addressed/unaddressed, allowing maintainers to track work items. In addition, two new events have been added to the ``/events`` API: ``cover-comment-created`` and ``patch-comment-created``. Recent versions of Python (3.10) and Django (3.2, 4.0) are now supported, while support for older Python (3.6) and Django (2.2, 3.0, 3.1) versions has been removed. More information on all the above is included below.


.. _Release Notes_v3.1.0_stable_3.1_New Features:

New Features
------------

- Patch comments and cover letter comments can be marked 'addressed' or 'unaddressed' to
  reflect whether the comment has been addressed by the patch and cover letter submitter
  or a reviewer. The current state of a comment is shown in the header when showing a
  comment and users with edit permission can toggle the state using an adjacent button.

- Two new event types have been added: ``cover-comment-created`` and
  ``patch-comment-created``. As their names would suggest, these track the
  creation of new cover letter and patch comments respectively.

- `Django 3.2 <https://docs.djangoproject.com/en/dev/releases/3.2/>`_ is now
  supported.

- `Django 4.0 <https://docs.djangoproject.com/en/dev/releases/4.0/>`_ is
  now supported.

- The ``Link`` header included in REST API responses now includes ``first``
  and ``last`` relations, as described in `RFC 5988`__. As their name would
  suggest, these can be used to navigate to the beginning and end of the
  resource.

  .. __: https://datatracker.ietf.org/doc/html/rfc5988

- `Python 3.10 <https://www.python.org/downloads/release/python-3100/>`_ is
  now supported.


.. _Release Notes_v3.1.0_stable_3.1_Upgrade Notes:

Upgrade Notes
-------------

- Django 3.0 is no longer supported. It is no longer supported upstream and
  most distributions provide a newer version.

- Django 3.1 is no longer supported. It is no longer supported upstream and
  most distributions provide a newer version.

- Python 3.6 is no longer supported. It is no longer supported upstream and
  most distributions provide a newer version.

- Django 2.2 is no longer supported. Is is no longer supported upstream and
  most distributions provide a newer version.

- Database configuration has been added to ``patchwork.settings.base``.
  Previously, this had to be specified in the ``settings.py`` file manually
  created by admins. The following environment variables can now be used to
  configure the settings:

  - ``DATABASE_TYPE`` (one of: ``postgres``, ``sqlite3``, ``mysql``;
    default: ``mysql``)
  - ``DATABASE_HOST`` (default: ``localhost``)
  - ``DATABASE_PORT`` (default: ``<unset>``)
  - ``DATABASE_NAME`` (default: ``patchwork``)
  - ``DATABASE_USER`` (default: ``patchwork``)
  - ``DATABASE_PASSWORD`` (default: ``patchwork``)

  If you are manually defining ``DATABASES`` in your ``settings.py`` file,
  this should have no impact. However, you may wish to rework your deployment
  to use environment variables instead.

- Database configuration variables ``PW_TEST_DB_*`` are renamed to their
  corresponding ``DATABASE_*`` names to sync development & production
  environments setup. Some mistaken references to ``DATABASE_PASS`` are
  also replaced with ``DATABASE_PASSWORD`` to follow the convention.


.. _Release Notes_v3.1.0_stable_3.1_Bug Fixes:

Bug Fixes
---------

- Fixed a compatability issue with Django 3.1 that prevented users from
  resetting their password.
  (`#394 <https://github.com/getpatchwork/patchwork/issues/394>`__)

- Comments and whitespace are now correctly stripped from the ``Message-ID``,
  ``In-Reply-To``, and ``References`` headers. One side effect of this change
  is that the parser is now stricter with regards to the format of the
  ``msg-id`` component of these headers: all identifiers must now be
  surrounded by angle brackets, e.g. ``<abcdef@example.com>``. This is
  mandated in the spec and a review of mailing lists archives suggest it is
  broadly adhered to. Without these markers, there is no way to delimit
  ``msg-id`` from any surrounding comments and whitespace.


.. _Release Notes_v3.1.0_stable_3.1_API Changes:

API Changes
-----------

- The API version has been updated to v1.3.

- A new REST API endpoint is available at ``/api/covers/<cover_id>/comments/<comment_id>/``.
  This can be used to retrieve and update (e.g. ``addressed`` state) details about a specific
  cover comment.

- A new REST API endpoint is available at ``/api/patches/<patch_id>/comments/<comment_id>/``.
  This can be used to retrieve and update (e.g. ``addressed`` state) details about a specific
  patch comment.

- The ``list_archive_url`` field will now be correctly shown for patch
  comments and cover letter comments.
  (`#391 <https://github.com/getpatchwork/patchwork/issues/391>`__)
