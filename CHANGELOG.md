# Change Log

All notable changes to this project will be documented in this file. Please
refer to the release notes for more detailed information, e.g. how to upgrade.

This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

- N/A

## [1.1.0] - 2016-03-03

### Added

- Python 3 support
- Web UI overhaul
- Check feature, which can be used to report the status of tests
- Automatic delegation of patches based on file path
- Automated documentation for the XML-RPC API. This can be found at the
  '/xmlrpc' in most Patchwork deployments
- Selenium-based UI tests
- Vagrant support for developers
- Assorted cleanup tasks and bug fixes

### Changed

- Patches can now be delegated to any Patchwork user
- Significant updates to the documentation

## [1.0.0] - 2015-10-26

### Added

- Patch tag infrastructure feature. This provide a quick summary of patch
  'tags' (e.g. `Acked-by`, `Reviewed-by`, ...) found in a patch and its replies
- Support for Django 1.7 and Django 1.8
- Support for Django Migrations. This will be the chosen method of making
  database changes going forward. See below for more information
- Support for tox
- Django management commands, which replace the existing Patchwork cron scripts
- CHANGELOG.md and UPGRADING.md docs

### Changed

- Static files are now gather and served using the `django.contrib.staticfiles`
  module, per Django best practices
- Restructured directory per modern Django standards. The `apps` directory no
  longer exists and Patchwork source has instead been moved to the top level
  directory
- Rewrote documentation to reflect changes in development and deployment best
  practices over the past few years
- Reworked `requirements.txt` and `settings.py` files

### Removed

- Support for Django 1.5
- Defunct Python 2.5 code
- Numerous dead files/code
- `bin/patchwork-cron` script, in favor of `cron` management command

### Deprecated

- Django 1.6 support will be removed in the next release
- Django 1.7 supports Django Migrations and Django 1.8 requires them. This
  negates the need for handwritten SQL migration scripts. Future releases will
  no longer include these scripts and they will eventually be removed

## [0.9.0] - 2015-03-22

**NOTE:** 1.0.0 was the first release of Patchwork adopting semantic versioning.
For information on *"0.9.0"* and before, please refer to Git logs.

[Unreleased]: https://github.com/getpatchwork/patchwork/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/getpatchwork/patchwork/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/getpatchwork/patchwork/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/getpatchwork/patchwork/compare/c561ebe...v0.9.0

