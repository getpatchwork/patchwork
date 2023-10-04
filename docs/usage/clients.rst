Clients
=======

A number of clients are available for interacting with Patchwork's various
APIs.

.. note::

   Got a client that you think might be useful to the broader community? Feel
   free to add it to this page by :doc:`submitting a patch
   </development/contributing>`.


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

The :program:`git-pw` application can be used to integrate Patchwork with Git.
The :program:`git-pw` application relies on the REST API and can be used to
interact to list, download and apply series, bundles and individual patches.

More information on :program:`git-pw`, including installation and usage
instructions, can be found in the `documentation`__ and the `GitHub repo`__.

__ https://git-pw.readthedocs.io/
__ https://github.com/getpatchwork/git-pw/


VSCode-Patchwork
----------------

The *Patchwork* VSCode plugin can be used to integrate Patchwork with VSCode.
This plugin relies on the REST API and can be used to view both patches and
series and to apply them locally. You can also browse patches and series and
look at replies.

More information on the *Patchwork* VSCode plugin can be found on the `VSCode
Marketplace`__ and the `GitHub repo`__.

__ https://marketplace.visualstudio.com/items?itemName=florent-revest.patchwork
__ https://github.com/FlorentRevest/vscode-patchwork


snowpatch
---------

The *snowpatch* application is a bridge between Patchwork and the Jenkins
continuous integration automation server. It monitors the REST API for incoming
patches, applies them on top of an existing git tree, triggers appropriate
builds and test suites, and reports the results back to Patchwork.

Find out more about :program:`snowpatch` at its `GitHub repo`__.

__ https://github.com/ruscur/snowpatch
