# Release Process

## Versioning

Since version 1.0, Patchwork has implemented a version of
[Semantic Versioning][ref-semver]. To summarise, releases take the format
**MAJOR.MINOR.PATCH** (or just **MAJOR.MINOR**). We increment:

1. **MAJOR** version when we make major UI changes or functionality updates
2. **MINOR** version when we make minor UI changes or functionality updates
3. **PATCH** version when we make make bug fixes, dependency updates etc.

In Git, each release will have a tag indicating the version number. In
addition, each release series has it's own branch called `stable/MAJOR.MINOR`
to allow backporting of bugfixes or security updates to older versions.

## Release Cycle

There is no cadence for releases: they are made available as necessary.

## Supported Versions

Typically all development should occur on `master`. While we will backport
bugfixes and security updates, we will not backport any new features. This
is to ensure stability for users of these versions of Patchwork.

## Release Checklist

* Documentation has been updated with latest release version
* Documentation references latest supported version of Django

[ref-semver]: http://semver.org/
