The REST API
============

Patchwork provides a REST API. This API can be used to retrieve and modify
information about patches, projects and more.

.. note::

   The REST API was introduced in Patchwork v2.0. Users of earlier Patchwork
   versions should instead refer to :doc:`xmlrpc`.

Documentation
-------------

Patchwork provides automatically generated documentation for the RESET API.
You can find this at the following URL:

    http://patchwork.example.com/api/

where `patchwork.example.com` refers to the URL of your Patchwork instance.

Interacting with the API
------------------------

REST APIs run over plain HTTP(S), thus, the API can be interfaced using
applications or libraries that support this widespread protocol. One such
application is `curl`__, which can be used to both retrieve and send
information to the REST API. For example, to get the version of the REST API
for a Patchwork instance hosted at `patchwork.example.com`, run:

.. code-block:: shell

    $ curl -s http://localhost:8000/api/1.0/ | python -m json.tool
    {
        "patches": "http://localhost:8000/api/1.0/patches/",
        "people": "http://localhost:8000/api/1.0/people/",
        "projects": "http://localhost:8000/api/1.0/projects/",
        "users": "http://localhost:8000/api/1.0/users/"
    }

In addition, a huge variety of libraries are avaiable for interacting with and
parsing the output of REST APIs. The `requests`__ library is wide-spread and
well-supported. To repeat the above example using `requests`:

.. code-block:: pycon

    $ python
    >>> import json
    >>> import requests
    >>> r = requests.get('http://patchwork.example.com/api/1.0/')
    >>> print(json.dumps(r.json(), indent=2))
    {
          "users": "http://localhost:8000/api/1.0/users/",
          "patches": "http://localhost:8000/api/1.0/patches/",
          "projects": "http://localhost:8000/api/1.0/projects/",
          "people": "http://localhost:8000/api/1.0/people/"
    }

Tools like `curl` and libraries like `requests` can be used to build anything
from small utilities to full-fledged clients targeting the REST API.

__ https://curl.haxx.se/
__ http://docs.python-requests.org/en/master/
