The REST API
============

Patchwork provides a REST API. This API can be used to retrieve and modify
information about patches, projects and more.

This guide provides an overview of how one can interact with the REST API. For
detailed information on type and response format of the various resources
exposed by the API, refer to the web browsable API. This can be found at:

    https://patchwork.example.com/api/1.0/

where `patchwork.example.com` refers to the URL of your Patchwork instance.

.. important::

   The REST API can be enabled/disabled by the administrator: it may not be
   available in every instance. Refer to ``/about`` on your given instance for
   the status of the API, e.g.

       https://patchwork.ozlabs.org/about

.. versionadded:: 2.0

   The REST API was introduced in Patchwork v2.0. Users of earlier Patchwork
   versions should instead refer to :doc:`XML-RPC API <xmlrpc>` documentation.

Getting Started
---------------

The easiest way to start experimenting with the API is to use the web browsable
API, as described above.

REST APIs run over plain HTTP(S), thus, the API can be interfaced using
applications or libraries that support this widespread protocol. One such
application is `curl`_, which can be used to both retrieve and send information
to the REST API. For example, to get the version of the REST API for a
Patchwork instance hosted at `patchwork.example.com`, run:

.. code-block:: shell

    $ curl -s 'https://patchwork.example.com/api/1.0/' | python -m json.tool
    {
        "bundles": "https://patchwork.example.com/api/1.0/bundles/",
        "covers": "https://patchwork.example.com/api/1.0/covers/",
        "events": "https://patchwork.example.com/api/1.0/events/",
        "patches": "https://patchwork.example.com/api/1.0/patches/",
        "people": "https://patchwork.example.com/api/1.0/people/",
        "projects": "https://patchwork.example.com/api/1.0/projects/",
        "series": "https://patchwork.example.com/api/1.0/series/",
        "users": "https://patchwork.example.com/api/1.0/users/"
    }


In addition, a huge variety of libraries are available for interacting with and
parsing the output of REST APIs. The `requests`_ library is wide-spread and
well-supported. To repeat the above example using `requests`:, run

.. code-block:: pycon

    $ python
    >>> import json
    >>> import requests
    >>> r = requests.get('https://patchwork.example.com/api/1.0/')
    >>> print(json.dumps(r.json(), indent=2))
    {
        "bundles": "https://patchwork.example.com/api/1.0/bundles/",
        "covers": "https://patchwork.example.com/api/1.0/covers/",
        "events": "https://patchwork.example.com/api/1.0/events/",
        "patches": "https://patchwork.example.com/api/1.0/patches/",
        "people": "https://patchwork.example.com/api/1.0/people/",
        "projects": "https://patchwork.example.com/api/1.0/projects/",
        "series": "https://patchwork.example.com/api/1.0/series/",
        "users": "https://patchwork.example.com/api/1.0/users/"
    }

Tools like `curl` and libraries like `requests` can be used to build anything
from small utilities to full-fledged clients targeting the REST API. For an
overview of existing API clients, refer to :doc:`../usage/clients`.

.. tip::

    While you can do a lot with existing installations, it's possible that you
    might not have access to all resources or may not wish to modify any
    existing resources. In this case, it might be better to :doc:`deploy your
    own instance of Patchwork locally <../development/installation>` and
    experiment with that instead.

Versioning
----------

By default, all requests will receive the latest version of the API: currently
``1.0``:

.. code-block:: http

    GET /api HTTP/1.1

You should explicitly request this version through the URL to prevent API
changes breaking your application:

.. code-block:: http

    GET /api/1.0 HTTP/1.1

Schema
------

Responses are returned as JSON. Blank fields are returned as ``null``, rather
than being omitted. Timestamps use the ISO 8601 format, times are by default
in UTC::

    YYYY-MM-DDTHH:MM:SSZ

Requests should use either query parameters or form-data, depending on the
method. Further information is provided `below <rest_parameters>`__.

Summary Representations
~~~~~~~~~~~~~~~~~~~~~~~

Some resources are particularly large or expensive to compute. When listing
these resources, a summary representation is returned that omits certain
fields.  To get all fields, fetch the detailed representation. For example,
listing patches will return summary representations for each patch:

.. code-block:: http

    GET /patches HTTP/1.1

Detailed Representations
~~~~~~~~~~~~~~~~~~~~~~~~

When fetching an individual resource, all fields will be returned. For example,
fetching a patch with an ID of ``123`` will return all available fields for
that particular resource:

.. code-block:: http

    GET /patches/123 HTTP/1.1

.. _rest_parameters:

Parameters
----------

Most API methods take optional parameters. For ``GET`` requests, these
parameters are mostly used for filtering and should be passed as a HTTP query
string parameters:

.. code-block:: shell

    $ curl 'https://patchwork.example.com/api/patches?state=under-review'

For all other types of requests, including ``POST`` and ``PATCH``, these
parameters should be passed as form-encoded data:

.. code-block:: shell

    $ curl -X PATCH -F 'state=under-review' \
      'https://patchwork.example.com/api/patches/123'

Authentication
--------------

Patchwork supports authentication using your username and password (basic
authentication) or with a token (token authentication). The latter is
recommended.

To authenticate with token authentication, you must first obtain a token. This
can be done from your profile, e.g. https://patchwork.example.com/profile.
Once you have a token, run:

.. code-block:: shell

    $ curl -H "Authorization: Token ${token}" \
        'https://patchwork.example.com/api/'

To authenticate using basic auth, you should use your Patchwork username and
password. To do this, run:

.. code-block:: shell

    $ curl -u ${username}:${password} \
        'https://patchwork.example.com/api/'

Not all resources require authentication. Those that do will return ``404 (Not
Found)`` if authentication is not provided to avoid leaking information.

Pagination
----------

Requests that return multiple items will be paginated by 30 items by default,
though this can vary from instance to instance. You can change page using the
``?page`` parameter. You can also set custom page sizes up to 100 on most
endpoints using the ``?per_page`` parameter.

.. code-block:: shell

    $ curl 'https://patchwork.example.com/api/patches?page=2&per_page=100'

Link Header
~~~~~~~~~~~

The `Link header`_ includes pagination information::

    Link: <https://patchwork.example.com/api/patches?page=3&per_page=100>; rel="next",
      <https://patchwork.example.com/api/patches?page=50&per_page=100>; rel="last"

The possible ``rel`` values are:

.. list-table::
   :header-rows: 1

   * - Name
     - Description
   * - ``next``
     - The link relation for the immediate next page of results.
   * - ``last``
     - The link relation for the last page of results.
   * - ``first``
     - The link relation for the first page of results.
   * - ``prev``
     - The link relation for the immediate previous page of results.

.. _curl: https://curl.haxx.se/
.. _requests: http://docs.python-requests.org/en/master/
.. _Link header: https://tools.ietf.org/html/rfc5988
