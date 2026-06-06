v2.2 Series ("Flannel")
=======================

.. _Release Notes_v2.2.4_stable_2.2:

v2.2.4
======

.. _Release Notes_v2.2.4_stable_2.2_API Changes:

API Changes
-----------

- The ``list_archive_url`` field will now be correctly shown for patch
  comments and cover letter comments.
  (`#391 <https://github.com/getpatchwork/patchwork/issues/391>`__)


.. _Release Notes_v2.2.3_stable_2.2:

v2.2.3
======

.. _Release Notes_v2.2.3_stable_2.2_Bug Fixes:

Bug Fixes
---------

- Resolve a bug that would prevent listing patches for a project via the
  browseable API view when logged in with admin permissions (`issue #379`__)

  __ https://github.com/getpatchwork/patchwork/issues/379


.. _Release Notes_v2.2.2_stable_2.2:

v2.2.2
======

.. _Release Notes_v2.2.2_stable_2.2_Bug Fixes:

Bug Fixes
---------

- An issue that preventing updating bundles via the REST API without
  updating the included patches has been resolved.
  (`#357 <https://github.com/getpatchwork/patchwork/issues/357>`__)

- The parser module now uses an atomic select-insert when creating new patch,
  cover letter and comment entries. This prevents the integrity errors from
  being logged in the DB logs.
  (`#358 <https://github.com/getpatchwork/patchwork/issues/358>`__)


.. _Release Notes_v2.2.1_stable_2.2:

v2.2.1
======

.. _Release Notes_v2.2.1_stable_2.2_API Changes:

API Changes
-----------

- The REST API now supports filtering patches and cover letters by message
  ID, using the ``msgid`` query parameter. Don't include leading or trailing
  angle brackets.


.. _Release Notes_v2.2.0_stable_2.2:

v2.2.0
======

.. _Release Notes_v2.2.0_stable_2.2_New Features:

New Features
------------

- Patches can now be related to other patches (e.g. to cross-reference
  revisions). Relations can be set via the REST API by maintainers
  (currently only for patches of projects they maintain). Patches can
  belong to at most one relation at a time.

- `Django 2.0 <https://docs.djangoproject.com/en/2.0/releases/2.0/>`_ is now
  supported. This requires Python 3.

- `Django 2.1 <https://docs.djangoproject.com/en/dev/releases/2.1/>`_ is now
  supported. This requires Python 3.

- `Django 2.2 <https://docs.djangoproject.com/en/dev/releases/2.2/>`_ is now
  supported. This requires Python 3.

- The ``patch-delegated``, ``patch-state-changed`` and ``check-created``
  events now have an ``actor`` associated with them - the user that updated
  the patch or created the check. For other event types, this attribute is
  present but unset.

- Add a field to Project to store a link to the project's mailing list
  archive, and display that on the project info page.

- Add a field to Project to store a URL format for a Message-ID redirector
  for the project's mailing list archive, and display a link to the email
  thread for each patch.

- Exporting patchwork projects as mbox files and optionally compressing them
  is now possible with the ``./manage exportproject`` management command.

- The URL schema now uses message IDs, rather than patch IDs, by
  default. Old URLs will redirect to the new URLs.

- `Python 3.7 <https://www.python.org/downloads/release/python-370/>`_ is now
  supported.

- `Python 3.8 <https://www.python.org/downloads/release/python-380/>`_ is now
  supported.


.. _Release Notes_v2.2.0_stable_2.2_Upgrade Notes:

Upgrade Notes
-------------

- `django-filter 1.1
  <https://github.com/carltongibson/django-filter/releases/tag/1.1.0>`_ is
  now supported.

- `django-filter 2.0
  <https://github.com/carltongibson/django-filter/releases/tag/2.0.0>`_ is
  now supported. This requires Python 3.

- `Django REST Framework 3.10
  <https://www.django-rest-framework.org/community/3.10-announcement/>`_ is
  now supported.

- `Django REST Framework 3.11
  <https://www.django-rest-framework.org/community/3.11-announcement/>`_ is
  now supported.

- `Django REST Framework 3.7
  <https://www.django-rest-framework.org/community/3.7-announcement/>`_ is now
  supported.

- `Django REST Framework 3.8
  <https://www.django-rest-framework.org/community/3.8-announcement/>`_ is now
  supported.

- `Django REST Framework 3.9
  <https://www.django-rest-framework.org/community/3.9-announcement/>`_ is now
  supported.

- Python 3.4 is no longer supported. This is no longer supported upstream and
  most distributions provide a newer version.

- Django 1.8, 1.9 and 1.10 are no longer supported. These are no longer
  supported upstream and most distributions provide a newer version.

- djangorestframework 3.4 and 3.5 are no longer supported. These were only
  used with Django 1.8 to 1.10 and are not compatible with any version
  now supported by Patchwork.

- ``pwclient`` is no longer packaged with Patchwork. Instead, it is developed
  as a separate project on `GitHub`__ and available from `PyPI`__.

  __ https://github.com/getpatchwork/pwclient
  __ https://pypi.org/project/pwclient/


.. _Release Notes_v2.2.0_stable_2.2_Bug Fixes:

Bug Fixes
---------

- CVE-2019-13122 has been fixed. Andrew Donnellan discovered an XSS
  via the message-id field. A malicious user could send a patch with
  a message ID that included a script tag. Because of the quirks of
  the email RFCs, such a message ID can survive being sent through
  many mail systems, including Gmail, and be parsed and stored by
  Patchwork. When a user viewed a patch detail page for the patch
  with this message id, the script would be run. This is fixed by
  properly escaping the field before it is rendered.

- Queries to the REST API with filters are now significantly faster: slow
  database queries were reworked.

- To avoid triggering spam filters due to failed signature validation, many
  mailing lists mangle the From header to change the From address to be the
  address of the list, typically where the sender's domain has a strict DMARC
  policy enabled. This leads to incorrect senders being recorded. We now try
  to unmangle the From header using the X-Original-From or Reply-To headers,
  as used by Google Groups and Mailman respectively.

- Assigning maintained projects when creating a new user in the admin page
  was causing an error. This is now resolved.

- Long headers can be wrapped using CRLF followed by WSP (whitespace). This
  whitespace was not being stripped, resulting in errant whitespace being
  saved for the patch subject. This is resolved though existing patches and
  cover letters will need to be updated manually.

- An issue that resulted in checks for all patches being listed for each
  patch is resolved.
  (`#203 <https://github.com/getpatchwork/patchwork/issues/203>`__)

- An issue that prevented updating of delegates using the REST API is
  resolved. (`#216 <https://github.com/getpatchwork/patchwork/issues/216>`__)

- A project's ``list_email``, ``list_id`` and ``link_name`` fields can no
  longer be updated via the REST API. This is a superuser-only operation
  that, for now, should only be done via the admin interface.
  (`#217 <https://github.com/getpatchwork/patchwork/issues/217>`__)

- It's now possible to assign patches to existing bundles from a user's TODO
  page.
  (`#213 <https://github.com/getpatchwork/patchwork/issues/213>`__)

- API resources with embedded series were not showing the ``web_url`` value
  for these series. This is now shown.

- Showing comments for a non-existant patch or cover letter was returning an
  empty response instead of a HTTP 404. This issue is resolved for both
  resources.

- Showing checks for a non-existant patch was returning an empty response
  instead of a HTTP 404. Similarly, attempting to create a new check against
  this patch would result in a HTTP 5xx error instead of a HTTP 404. Both
  issues are now resolved.

- Fields added in API v1.1 are now consistently excluded when requesting API
  v1.0, as was intended.

- `#197`__ was the result of a issue with OzLabs instance and not Patchwork
  itself, and the fix included actually ended up corrupting subjects for
  everyone. It has now been reverted.

  __ https://github.com/getpatchwork/patchwork/issues/197

- The ``pwclientrc`` samples generated by Patchwork were previously not valid
  INI files. This issue is resolved. (`#277
  <https://github.com/getpatchwork/patchwork/issues/277>`__)

- A bug that would result in patches from later series revisions being
  included in earlier revisions has been resolved.

- Previously, attempting to retrieve a patch that did not exist would result
  in a ``HTTP 500`` (Internal Server Error) being raised. This has been
  corrected and a ``HTTP 404`` (Not Found) is now raised instead.

- In the past, Patchwork used to support filtering patches that weren't
  delegated to anyone. This feature was removed in v1.1.0, as part of a patch
  designed to support delegation to anyone. However, that feature didn't scale
  and was later removed. The ability to delegate to anyone is now itself
  re-introduced.

- The delegate and submitter fields will remain populated when moving
  between different pages or changing filters.
  (`#78 <https://github.com/getpatchwork/patchwork/issues/78>`__)


.. _Release Notes_v2.2.0_stable_2.2_API Changes:

API Changes
-----------

- Relations are available via ``/patches/{patchID}/`` endpoint, in
  the ``related`` field.

- Allow ordering events from the events API by date. This can be done by
  adding ``order=date`` or ``order=-date`` (the default) parameters.

- The ``/event`` API now exposes an ``actor`` attribute. It is possible to
  filter events by this attribute.

- The API version has been updated to v1.2.

- Projects now expose the ``list_archive_url`` and
  ``list_archive_url_format`` attributes.

- Patches, comments and cover letters now expose a ``list_archive_url``
  attribute.

- The REST API now supports filtering patches by their hashes, using the
  ``hash`` query parameter.

- Bundles can now be created, updated and deleted via the REST API.


.. _Release Notes_v2.2.0_stable_2.2_Security Notes:

Security Notes
--------------

- Change the recommended method for generating the Django secret key to use a
  cryptographically secure random number generator.


.. _Release Notes_v2.2.0_stable_2.2_Other Notes:

Other Notes
-----------

- The performance of various pages has been improved with the addition of
  some database indexes and optimization of some queries.
