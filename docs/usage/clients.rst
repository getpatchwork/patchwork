Clients
=======

A number of clients are available for interacting with Patchwork's various
APIs.

pwclient
--------

The `pwclient` application, provided with Patchwork, can be used to interact
with Patchwork from the command line. Functionality provided by `pwclient`
includes:

- Listing patches, projects, and checks
- Downloading and applying patches to a local code base
- Modifying the status of patches
- Creating new checks

`pwclient` can be downloaded from the `Ozlabs Patchwork instance`__, or at the
following path for most other Patchwork instances:

    http://patchwork.example.com/pwclient/

where `patchwork.example.com` corresponds to the URL a Patchwork instance is
hosted at.

Once downloaded, view information about all the operations supported by
`pwclient`, run:

.. code-block:: shell

    $ pwclient --help

__ https://patchwork.ozlabs.org/pwclient/

git-pw
------

The `git-pw` application can be used to integrate Git with Patchwork. The
`git-pw` application relies on the REST API and can be used to interact to
list, download and apply series, bundles and individual patches.

More information on `git-pw`, including installation and usage instructions,
can be found in the `documentation`__ and the `GitHub repo`__.

__ https://git-pw.readthedocs.io/
__ https://github.com/getpatchwork/git-pw
