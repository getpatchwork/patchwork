# The XML-RPC API

**NOTE:** This guide covers usage information for the Patchwork XML-RPC API.
For information on developing custom applications or clients for this API,
refer to the [developers documentation][doc-development].

Patchwork provides an XML-RPC API. This API can be used to be used to retrieve
and modify information about patches, projects and more.

**NOTE:** The XML-RPC API can be enabled/disabled by the administrator: it may
not be available in every instance.

## pwclient

The `pwclient` application, provided with Patchwork, can be used to interact
with Patchwork from the command line. Functionality provided by `pwclient`
includes:

* Listing patches, projects, and checks
* Downloading and applying patches to a local code base
* Modifying the status of patches
* Creating new checks

pwclient can be downloaded from the [Ozlabs Patchwork instance][ref-pw-oz], or
at the following path for other Patchwork instances:

    http://patchwork.example.com/pwclient/

where `patchwork.example.com` corresponds to the URL a Patchwork instance is
hosted at.

Once downloaded, to view information about all the operations supported by
`pwclient`, run:

    $ pwclient --help

[doc-development]: ../development/xmlrpc.md
