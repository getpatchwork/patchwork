Configuration
=============

This document describes the various configuration options available in
Patchwork. These options can be used for both :doc:`development
<../development/installation>` and :doc:`deployment <installation>`
installations.

The ``settings.py`` File
------------------------

Patchwork is a Django application and, as such, relies on Python-based settings
files. Refer to the `Django documentation`__ for more information on the
general format.

Patchwork provides three settings files:

``base.py``
  A base settings file that should not be used directly.

``dev.py``
  A settings file for development use. **This file is horribly insecure and
  must not be used in production**.

``production.example.py``
  A sample settings file for production use. This will likely require some
  heavy customization. The :ref:`deployment guide <deployment-settings>`
  provides more information.

__ https://docs.djangoproject.com/en/2.2/topics/settings/

Patchwork-specific Settings
---------------------------

Patchwork utilizes a number of Patchwork-only settings in addition to the
`Django`__ and `Django REST Framework`__ settings.

__ https://docs.djangoproject.com/en/2.2/ref/settings/
__ http://www.django-rest-framework.org/api-guide/settings/

``ADMINS_HIDE``
~~~~~~~~~~~~~~~

If True, the details in `ADMINS`__ will be hidden from the *About* page
(``/about``).

.. versionadded:: 2.2

__ https://docs.djangoproject.com/en/2.2/ref/settings/#admins

``COMPAT_REDIR``
~~~~~~~~~~~~~~~~

Enable redirections of URLs from previous versions of Patchwork.

``CONFIRMATION_VALIDITY_DAYS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of days to consider an account confirmation request valid. After
this interval, the :ref:`cron management command <deployment-final-steps>` will
delete the request.

``DEFAULT_ITEMS_PER_PAGE``
~~~~~~~~~~~~~~~~~~~~~~~~~~

The default number of items to display in the list pages for a project
(``/project/{projectID}/list``) or bundle (``/bundle/{userID}/{bundleName}``).

This is customizable on a per-user basis from the user configuration page.

.. versionchanged:: 2.0

    This option was previously named ``DEFAULT_PATCHES_PER_PAGE``. It was
    renamed as cover letters are now supported also.

``ENABLE_REST_API``
~~~~~~~~~~~~~~~~~~~

Enable the :doc:`REST API <../api/rest/index>`.

.. versionadded:: 2.0

``ENABLE_XMLRPC``
~~~~~~~~~~~~~~~~~

Enable the :doc:`XML-RPC API <../api/xmlrpc>`.

.. TODO(stephenfin) Deprecate this in favor of SECURE_SSL_REDIRECT

``FORCE_HTTPS_LINKS``
~~~~~~~~~~~~~~~~~~~~~

Force use of ``https://`` links instead of guessing the scheme based on current
access. This is useful if SSL protocol is terminated upstream of the server
(e.g. at the load balancer)

``MAX_REST_RESULTS_PER_PAGE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The maximum number of items that can be requested in a REST API request using
the ``per_page`` parameter.

.. versionadded:: 2.2

``NOTIFICATION_DELAY_MINUTES``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of minutes to wait before sending any notifications to a user. An
notification generated during this time are gathered into a single digest
email, ensuring users are not spammed with emails from Patchwork.

``NOTIFICATION_FROM_EMAIL``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The email address that notification emails should be sent from.

``REST_RESULTS_PER_PAGE``
~~~~~~~~~~~~~~~~~~~~~~~~~

The number of items to include in REST API responses by default. This can be
overridden by the ``per_page`` parameter for some endpoints.

.. versionadded:: 2.0
