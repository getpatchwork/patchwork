Patchwork
=========

Patchwork is a patch tracking system for community-based projects. It is
intended to make the patch management process easier for both the project's
contributors and maintainers, leaving time for the more important (and more
interesting) stuff.

Patches that have been sent to a mailing list are 'caught' by the system, and
appear on a web page. Any comments posted that reference the patch are appended
to the patch page too. The project's maintainer can then scan through the list
of patches, marking each with a certain state, such as Accepted, Rejected or
Under Review. Old patches can be sent to the archive or deleted.

Currently, Patchwork is being used for a number of open-source projects, mostly
subsystems of the Linux kernel. Although Patchwork has been developed with the
kernel workflow in mind, the aim is to be flexible enough to suit the majority
of community projects.

.. _user-docs:

.. toctree::
   :maxdepth: 2
   :caption: User Documentation

   usage/overview
   usage/design
   usage/delegation
   usage/headers
   usage/clients

.. _deployment-docs:

.. toctree::
   :maxdepth: 2
   :caption: Deployment Documentation

   deployment/installation
   deployment/configuration
   deployment/management
   deployment/upgrading

.. _development-docs:

.. toctree::
   :maxdepth: 2
   :caption: Development Documentation

   development/contributing
   development/installation
   development/releasing
   development/api
   development/assets

.. _api-docs:

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   api/rest
   api/xmlrpc

.. _release-note-docs:

.. toctree::
   :maxdepth: 2
   :caption: Release Notes

   releases/unreleased
   releases/dazzle
   releases/cashmere
   releases/burlap
   releases/alpaca
