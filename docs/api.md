# The XML-RPC API

Patchwork provides an XML-RPC API. This API can be used to be used to retrieve
and modify information about patches, projects and more.

**NOTE:** The XML-RPC API can be enabled/disabled by the administrator: it may
not be available in every instance.

## Patchwork API Documentation

Patchwork provides automatically generated documentation for the XML-RPC API.
You can find this at the following URL:

    http://patchwork.example.com/xmlrpc/

Where `patchwork.example.com` refers to the URL of your patchwork instance.

**NOTE:** Automatic documentation generation for the patchwork API was
introduced in Patchwork v1.1. Prior versions of Patchwork do not offer this
functionality.

## Developing Your Own Client

You need to connect to the server. Some methods require authentication (via
HTTP Basic Auth) while others do not. Authentication uses your patchwork
account and the on-server documention will indicate where it is necessary.
We will only cover the unauthenticated method here for brevity - please
consult the [`xmlrpclib`] documentation for more detailed examples:

    from __future__ import print_function
    import sys
    import xmlrpclib

    url = 'http://patchwork.example.org/xmlrpc/'

    try:
        rpc = xmlrpclib.ServerProxy(url)
    except:
        print('Unable to connect to %s\n' % url, file=sys.stderr)
        sys.exit(1)

After connecting, the `rpc` object will be populated with a list of available
functions (or procedures, in RPC terminology). For example, if we continue
with the above example:

    print(rpc.pw_rpc_version())

It should be possible to use all the methods listed in the
[server's documentation](#patchwork-api-documentation).

[`xmlrpclib`]: https://docs.python.org/2/library/xmlrpclib.html
