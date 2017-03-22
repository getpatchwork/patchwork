The XML-RPC API
===============

Patchwork provides an XML-RPC API. This API can be used to be used to retrieve
and modify information about patches, projects and more.

This guide covers development information for the Patchwork XML-RPC API. For
information on using the REST API, refer to `rest`. For information on general
usage of the XML-RPC API, refer to :doc:`../usage/xmlrpc`.

.. note::

   The XML-RPC API can be enabled/disabled by the administrator: it may not be
   available in every instance.

Documentation
-------------

Patchwork provides automatically generated documentation for the XML-RPC API.
You can find this at the following URL:

    http://patchwork.example.com/xmlrpc/

where `patchwork.example.com` refers to the URL of your Patchwork instance.

.. note::

   Automatic documentation generation for the Patchwork API was introduced in
   Patchwork v1.1. Prior versions of Patchwork do not offer this functionality.

Interacting with the API
------------------------

The Patchwork XML-RPC API provides a number of "methods". Some methods require
authentication (via HTTP Basic Auth) while others do not. Authentication uses
your Patchwork account and the on-server documentation will indicate where it
is necessary. We will only cover the unauthenticated method here for brevity -
consult the `xmlrpclib`__ documentation for more detailed examples:

To interact with the Patchwork XML-RPC API, a XML-RPC library should be used.
Python provides such a library - `xmlrpclib` - in its standard library. For
example, to get the version of the XML-RPC API for a Patchwork instance hosted
at `patchwork.example.com`, run:

.. code-block:: pycon

    $ python
    >>> import xmlrpclib  # or 'xmlrpc.client' for Python 3
    >>> rpc = xmlrpclib.ServerProxy('http://patchwork.example.com/xmlrpc/')
    >>> rpc.pw_rpc_version()
    1.1

Once connected, the `rpc` object will be populated with a list of available
functions (or procedures, in RPC terminology). In the above example, we used
the `pw_rpc_version` method, however, it should be possible to use all the
methods listed in the server documentation.

__ https://docs.python.org/2/library/xmlrpclib.html
