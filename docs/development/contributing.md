# Tips and Tricks

## Coding Standards

**Follow PEP8**. All code is currently PEP8 compliant and it should stay this
way.

Changes that fix semantic issues will be generally be happily received, but
please keep such changes separate from functional changes.

`pep8` targets are provided via tox. Refer to the [testing section](#testing)
below for more information on usage of this tool.

## Testing

Patchwork includes a [tox][ref-tox] script to automate testing. This requires
a functional database and some Python requirements like `tox`. Please refer
to the [development guide][doc-development] for information on how to configure
these.

Assuming these requirements are met, actually testing Patchwork is quite easy
to do. To start, you can show the default targets like so:

    $ tox --list

You'll see that this includes a number of targets to run unit tests against
the different versions of Django supported, along with some other targets
related to code coverage and code quality. To run one of these, use the `-e`
parameter:

    $ tox -e py27-django18

In the case of the unit tests targets, you can also run specific tests by
passing the fully qualified test name as an additional argument to this
command:

    $ tox -e py27-django18 patchwork.tests.SubjectCleanUpTest

Because Patchwork support multiple versions of Django, it's very important
that you test against all supported versions. When run without argument, tox
will do this:

    $ tox

## Submitting Changes

All patches should be sent to the [mailing list][pw-ml]. When doing so, please
abide by the [QEMU guidelines][ref-qemu-contrib] on contributing or submitting
patches. This covers both the initial submission and any follow up to the
patches. In particular, please ensure:

* [All tests pass](#testing)
* Documentation has been updated with new requirements, new script names etc.
* The `CHANGES` file has been updated with any added or removed features

[doc-development]: installation.md
[pw-ml]: https://ozlabs.org/mailman/listinfo/patchwork
[ref-qemu-contrib]: http://wiki.qemu.org/Contribute/SubmitAPatch
[ref-tox]: https://tox.readthedocs.io/en/latest/
