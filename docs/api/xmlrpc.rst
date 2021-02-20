The XML-RPC API
===============

Patchwork provides an XML-RPC API. This API can be used to be used to retrieve
and modify information about patches, projects and more.

.. important::

   The XML-RPC API can be enabled/disabled by the administrator: it may not be
   available in every instance. Refer to ``/about`` on your given instance for
   the status of the API, e.g.

       https://patchwork.ozlabs.org/about

   Alternatively, simply attempt to make a request to the API.

.. deprecated:: 2.0

    The XML-RPC API is a legacy API and has been deprecated in favour of the
    :doc:`REST API <rest/index>`. It may be removed in a future release.

Getting Started
---------------

The Patchwork XML-RPC API provides a number of "methods". Some methods require
authentication (via HTTP Basic Auth) while others do not. Authentication uses
your Patchwork account and the on-server documentation will indicate where it
is necessary. We will only cover the unauthenticated method here for brevity -
consult the `xmlrpc`_ documentation for more detailed examples:

To interact with the Patchwork XML-RPC API, a XML-RPC library should be used.
Python provides such a library - `xmlrpc`_ - in its standard library. For
example, to get the version of the XML-RPC API for a Patchwork instance hosted
at `patchwork.example.com`, run:

.. code-block:: pycon

    $ python
    >>> import xmlrpc.client
    >>> rpc = xmlrpc.client.ServerProxy('http://patchwork.example.com/xmlrpc/')
    >>> rpc.pw_rpc_version()
    1.1

Once connected, the ``rpc`` object will be populated with a list of available
functions (or procedures, in RPC terminology). In the above example, we used
the ``pw_rpc_version`` method, however, it should be possible to use all the
methods listed in the server documentation.

Further Information
-------------------

Patchwork provides automatically generated documentation for the XML-RPC API.
You can find this at the following URL:

    https://patchwork.example.com/xmlrpc/

where `patchwork.example.com` refers to the URL of your Patchwork instance.

.. versionchanged:: 1.1

   Automatic documentation generation for the Patchwork API was introduced in
   Patchwork v1.1. Prior versions of Patchwork do not offer this functionality.

.. _xmlrpc: https://docs.python.org/3/library/xmlrpc.html
