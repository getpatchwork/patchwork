Clients
=======

A number of clients are available for interacting with Patchwork's various
APIs.


pwclient
--------

.. versionchanged:: 2.2

   :program:`pwclient` was previously provided with Patchwork. It has been
   packaged as a separate application since Patchwork v2.2.0.

The :program:`pwclient` application can be used to interact with Patchwork from
the command line. Functionality provided by :program:`pwclient` includes:

- Listing patches, projects, and checks
- Downloading and applying patches to a local code base
- Modifying the status of patches
- Creating new checks

More information on :program:`pwclient`, including installation and usage
instructions, can be found in the `documentation`__ and the `GitHub repo`__.

__ https://pwclient.readthedocs.io/
__ https://github.com/getpatchwork/pwclient/


git-pw
------

The :program:`git-pw` application can be used to integrate Git with Patchwork.
The :program:`git-pw` application relies on the REST API and can be used to
interact to list, download and apply series, bundles and individual patches.

More information on :program:`git-pw`, including installation and usage
instructions, can be found in the `documentation`__ and the `GitHub repo`__.

__ https://git-pw.readthedocs.io/
__ https://github.com/getpatchwork/git-pw/


snowpatch
---------

The :program:`snowpatch` application is a bridge between Patchwork and the
Jenkins continuous integration automation server. It monitors the REST API
for incoming patches, applies them on top of an existing git tree, triggers
appropriate builds and test suites, and reports the results back to Patchwork.

Find out more about :program:`snowpatch` at its `GitHub repo`__.

__ https://github.com/ruscur/snowpatch
