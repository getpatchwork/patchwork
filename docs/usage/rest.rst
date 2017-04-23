The REST API
============

.. note::

   This guide covers usage information for the Patchwork REST API. For
   information on using the XML-RPC API, refer to :doc:`xmlrpc`. For
   information on developing custom applications or clients for this API, refer
   to the :doc:`../development/rest`.

Patchwork provides a REST API. This API can be used to retrieve and modify
information about patches, projects and more.

.. important::

   The REST API can be enabled/disabled by the administrator: it may not be
   available in every instance. Refer to ``/about`` on your given instance for
   the status of the API, e.g.

       https://patchwork.ozlabs.org/about

.. versionadded:: 2.0

   The REST API was introduced in Patchwork v2.0. Users of earlier Patchwork
   versions should instead refer to :doc:`xmlrpc`.

git-pw
------

The `git-pw` application can be used to integrate Git with Patchwork. The
`git-pw` application relies on the REST API and can be used to interact to
list, download and apply series, bundles and individual patches.

More information on `git-pw`, including installation and usage instructions,
can be found in the `documentation`__ and the `GitHub repo`__.

__ https://git-pw.readthedocs.io/
__ https://github.com/getpatchwork/git-pw
