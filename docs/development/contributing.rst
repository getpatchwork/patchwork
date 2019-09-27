Contributing
============

Coding Standards
----------------

**Follow PEP8**. All code is currently `PEP 8`_ compliant and it should stay
this way.

All code must be licensed using `GPL v2.0 or later`_ and must have a `SPDX
License Identifier`_ stating this. A copyright line should be included on new
files and may be added for significant changes to existing files.

.. code-block:: python

   # Patchwork - automated patch tracking system
   # Copyright (C) 2000 Jane Doe <jane.doe@example.com>
   # Copyright (C) 2001 Joe Bloggs <joebloggs@example.com>
   #
   # SPDX-License-Identifier: GPL-2.0-or-later

Changes that fix semantic issues will be happily received, but please keep such
changes separate from functional changes.

Patchwork uses the `pre-commit`_ framework to allow automated style checks when
committing code. This is opt-in but avoids the need to manually run style
checks on commits. Pre-commit can be installed and enabled like so:

.. code-block:: shell

   $ pip install --user pre-commit
   $ pre-commit install --allow-missing-config

Once installed, the various checks listed in ``.pre-commit-config.yaml`` will
be run on changed files when committing. It is also possible to run the checks
on all files manually:

.. code-block:: shell

   $ pre-commit run --all-files

In addition to *pre-commit*, we provide *tox* targets for style checks. These
are used by CI and can be useful if checking all files manually. Refer to the
:ref:`testing` section below for more information on usage of this tool.

.. _testing:

Testing
-------

Patchwork includes a `tox`_ script to automate testing. This requires a
functional database and some Python requirements like *tox*. Refer to
:doc:`installation` for information on how to configure these.

You may also need to install *tox*. If so, do this now:

.. code-block:: shell

   $ pip install --user tox

.. tip::

   If you're using Docker, you may not need to install *tox*
   locally. Instead, it will already be installed inside the
   container. For Docker, you can run *tox* like so:

   .. code-block:: shell

      $ docker-compose run --rm web tox [ARGS...]

   For more information, refer to :ref:`installation-docker`.

Assuming these requirements are met, actually testing Patchwork is quite easy
to do. To start, you can show the default targets like so:

.. code-block:: shell

   $ tox -l

You'll see that this includes a number of targets to run unit tests against the
different versions of Django supported, along with some other targets related
to code coverage and code quality. To run one of these, use the ``-e``
parameter:

.. code-block:: shell

   $ tox -e py27-django18

In the case of the unit tests targets, you can also run specific tests by
passing the fully qualified test name as an additional argument to this
command:

.. code-block:: shell

   $ tox -e py27-django18 patchwork.tests.SubjectCleanUpTest

Because Patchwork support multiple versions of Django, it's very important that
you test against all supported versions. When run without argument, tox will do
this:

.. code-block:: shell

   $ tox


.. _release-notes:

Release Notes
-------------

Patchwork uses `reno`_ for release note management. To use *reno*, you must
first install it:

.. code-block:: shell

   $ pip install --user reno

Once installed, a new release note can be created using the ``reno new``
command:

.. code-block:: shell

   $ reno new <slugified-summary-of-change>

Modify the created file, removing any irrelevant sections, and include the
modified file in your change.


API
---

As discussed in :doc:`releasing`, the API is versioned differently from
Patchwork itself. Should you make changes to the API, you need to ensure these
only affect newer versions of the API. Refer to previous changes in the
``patchwork/api`` directory and to the `Django REST Framework documentation`_
for more information.

.. important::

    All API changes should be called out in :ref:`release notes
    <release-notes>` using the ``api`` section.


Reporting Issues
----------------

You can report issues to the :ref:`mailing list <mailing-lists>` or the `GitHub
issue tracker`_.


Submitting Changes
------------------

All patches should be sent to the :ref:`mailing list <mailing-lists>`. You must
be subscribed to the list in order to submit patches. Please abide by the `QEMU
guidelines`_ on contributing or submitting patches. This covers both the
initial submission and any follow up to the patches. In particular, ensure:

* :ref:`All tests pass <testing>`

* Documentation has been updated with new requirements, new script names etc.

* :ref:`A release note is included <release-notes>`

Patches should ideally be submitted using the *git send-email* tool.


.. _mailing-lists:

Mailing Lists
-------------

Patchwork uses a single mailing list for development, questions and
announcements.

    patchwork@lists.ozlabs.org

Further information about the Patchwork mailing list is available can be found on
`lists.ozlabs.org`_.

.. _PEP 8: https://pep8.org/
.. _GPL v2.0 or later: https://spdx.org/licenses/GPL-2.0-or-later.html
.. _SPDX License Identifier: https://spdx.org/using-spdx-license-identifier
.. _pre-commit: https://pre-commit.com/
.. _tox: https://tox.readthedocs.io/en/latest/
.. _reno: https://docs.openstack.org/developer/reno/
.. _QEMU guidelines: http://wiki.qemu.org/Contribute/SubmitAPatch
.. _Django REST Framework documentation: http://www.django-rest-framework.org/api-guide/versioning/
.. _GitHub issue tracker: https://github.com/getpatchwork/patchwork
.. _lists.ozlabs.org: https://lists.ozlabs.org/listinfo/patchwork
