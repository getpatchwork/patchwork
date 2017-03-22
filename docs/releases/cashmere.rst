v1.1 Series ("Cashmere")
========================

1.1.3
-----

This release fixes a number of issues with the 1.1.2 release.

Bug Fixes
~~~~~~~~~

- Some Python 3 issues are resolved in `pwclient`

- `pwclient` now functions as expected behind a proxy

1.1.2
-----

This release fixed a number of issues with the 1.1.1 release.

Bug Fixes
~~~~~~~~~

- Headers containing invalid characters or codings are now parsed correctly

- Patches can no longer be delegated to any user

  This had significant performance impacts and has been reverted.

1.1.1
-----

This release fixed a number of issues with the 1.1.0 release.

Bug Fixes
~~~~~~~~~

- Numerous issues in the `parsemail.py`, `parsearchive.py` and `parsemail.sh`
  scripts are resolved

- Permissions of database tables, as set by `grant-all` SQL scripts, are now
  set for tables added in Patchwork 1.1.0

- Some performance and usability regressions in the UI are resolved

1.1.0
-----

This release focuses on usability and maintainability, and sets us up nicely
for a v2.0.0 release in the near future. Feature highlights of v1.1.0 include:

- Automated delegation of patches, based on the files modified in said patches.

- Storing of test results, a.k.a. "checks", on a patch-by-patch basis.

- Delegation of patches to any registered Patchwork user (previously one had to
  be a registered maintainer).

- Overhaul of the web UI, which is now based on Bootstrap.

- Python 3 support.

New Features
~~~~~~~~~~~~

- The web UI is updated to reflect modern web standards. Bootstrap 3.x is used.

- Python 3.4 is now supported

- Checks, which can be used to report the status of tests, have been added

- Automatic delegation of patches based on file path

- Automated documentation for the XML-RPC API. This can be found at the
  '/xmlrpc' in most Patchwork deployments

- Vagrant is now integrated for use during development

Upgrade Notes
~~~~~~~~~~~~~

- Patches can now be delegated to any Patchwork user.
