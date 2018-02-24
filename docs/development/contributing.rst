Contributing
============

Coding Standards
----------------

**Follow PEP8**. All code is currently PEP8 compliant and it should stay this
way.

Changes that fix semantic issues will be generally be happily received, but
please keep such changes separate from functional changes.

`pep8` targets are provided via tox. Refer to the :ref:`testing` section
below for more information on usage of this tool.

.. _testing:

Testing
-------

Patchwork includes a `tox`_ script to automate testing. This requires a
functional database and some Python requirements like `tox`. Refer to
:doc:`installation` for information on how to configure these.

You may also need to install `tox`. If so, do this now:

.. code-block:: shell

   $ sudo pip install tox

.. tip::

   If you're using Docker, you may not need to install `tox`
   locally. Instead, it will already be installed inside the
   container. For Docker, you can run `tox` like so:

   .. code-block:: shell

      $ docker-compose run web tox [ARGS...]

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

Patchwork uses `reno`_ for release note management. To use `reno`, you must
first install it:

.. code-block:: shell

   $ sudo pip install tox

Once installed, a new release note can be created using the ``reno new``
command:

.. code-block:: shell

   $ reno new <slugified-summary-of-change>

Modify the created file, removing any irrelevant sections, and include the
modified file in your change.

Submitting Changes
------------------

All patches should be sent to the `mailing list`_. When doing so, please abide
by the `QEMU guidelines`_ on contributing or submitting patches. This covers
both the initial submission and any follow up to the patches. In particular,
ensure:

* :ref:`All tests pass <testing>`

* Documentation has been updated with new requirements, new script names etc.

* :ref:`A release note is included <release-notes>`

.. _tox: https://tox.readthedocs.io/en/latest/
.. _reno: https://docs.openstack.org/developer/reno/
.. _mailing list: https://ozlabs.org/mailman/listinfo/patchwork
.. _QEMU guidelines: http://wiki.qemu.org/Contribute/SubmitAPatch
