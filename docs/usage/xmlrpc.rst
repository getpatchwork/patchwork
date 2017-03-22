The XML-RPC API
===============

.. note::

   This guide covers usage information for the Patchwork XML-RPC API.  For
   information on using the REST API, refer to :doc:`rest`. For information on
   developing custom applications or clients for this API, refer to the
   `../development/xmlrpc`.

Patchwork provides an XML-RPC API. This API can be used to be used to retrieve
and modify information about patches, projects and more.

.. note::

   The XML-RPC API can be enabled/disabled by the administrator: it may not be
   available in every instance.

pwclient
--------

The `pwclient` application, provided with Patchwork, can be used to interact
with Patchwork from the command line. Functionality provided by `pwclient`
includes:

* Listing patches, projects, and checks
* Downloading and applying patches to a local code base
* Modifying the status of patches
* Creating new checks

pwclient can be downloaded from the `Ozlabs Patchwork instance`__, or at the
following path for other Patchwork instances:

    http://patchwork.example.com/pwclient/

where `patchwork.example.com` corresponds to the URL a Patchwork instance is
hosted at.

Once downloaded, to view information about all the operations supported by
`pwclient`, run:

.. code-block:: shell

    $ pwclient --help

__ https://patchwork.ozlabs.org/pwclient/
