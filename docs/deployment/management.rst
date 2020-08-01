Management
==========

This document describes the myriad administrative commands available with
Patchwork. Many of these commands are referenced in the :doc:`development
<../development/installation>` and :doc:`deployment <installation>`
installation guides.

The ``manage.py`` Script
------------------------

Django provides the ``django-admin`` command-line utility for interacting with
Django applications and projects, as described in the `Django documentation`_.
Patchwork, being a Django application, provides a wrapper for this command -
``manage.py`` - that exposes not only the management commands of Django and its
default applications, but also a number of custom, Patchwork-only management
commands.

An overview of the Patchwork-specific commands is provided below. For
information on the commands provided by Django itself, refer to the `Django
documentation`_. Information on any command can also be found by passing the
``--help`` parameter:

.. code-block:: shell

   ./manage.py cron --help

.. _Django documentation: https://docs.djangoproject.com/en/1.8/ref/django-admin/

Available Commands
------------------

cron
~~~~

.. program:: manage.py cron

.. code-block:: shell

   ./manage.py cron

Run periodic Patchwork functions: send notifications and expire unused users.

This is required to ensure notifications emails are actually sent to users that
request them and is helpful to expire unused users created by spambots. For
more information on integration of this script, refer to the :ref:`deployment
installation guide <deployment-cron>`.

dumparchive
~~~~~~~~~~~

.. program:: manage.py dumparchive

Export Patchwork projects as tarball of mbox files.

.. code-block:: shell

   ./manage.py dumparchive [-c | --compress] [PROJECT [PROJECT...]]

This is mostly useful for exporting the patch dataset of a Patchwork project
for use with other programs.

.. option:: -c, --compress

   compress generated archive.

.. option:: PROJECT

   list ID of project(s) to export. Export all projects if none specified.

parsearchive
~~~~~~~~~~~~

.. program:: manage.py parseachive

Parse an mbox archive file and store any patches/comments found.

.. code-block:: shell

   ./manage.py parsearchive [--list-id <list-id>] <infile>

This is mostly useful for development or for adding message that were missed
due to, for example, an outage.

.. option:: --list-id <list-id>

   mailing list ID. If not supplied, this will be extracted from the mail
   headers.

.. option:: infile

   input mbox filename

parsemail
~~~~~~~~~

.. program:: manage.py parsemail

Parse an mbox file and store any patch/comment found.

.. code-block:: shell

   ./manage.py parsemail [--list-id <list-id>] <infile>

This is the main script used to get mails (and therefore patches) into
Patchwork. It is generally used by the ``parsemail.sh`` script in combination
with a mail transfer agent (MTA) like Postfix. For more information, refer to
the :ref:`deployment installation guide <deployment-parsemail>`.

.. option:: --list-id <list-id>

   mailing list ID. If not supplied, this will be extracted from the mail
   headers.

.. option:: infile

   input mbox filename. If not supplied, a patch will be read from ``stdin``.

replacerelations
~~~~~~~~~~~~~~~~

.. program:: manage.py replacerelations

Parse a patch groups file and store any relation found

.. code-block:: shell

    ./manage.py replacerelations <infile>

This is a script used to ingest relations into Patchwork.

A patch groups file contains on each line a list of space separated patch IDs
of patches that form a relation.

For example, consider the contents of a sample patch groups file::

    1 3 5
    2
    7 10 11 12

In this case the script will identify 2 relations, (1, 3, 5) and
(7, 10, 11, 12). The single patch ID "2" on the second line is ignored as a
relation always consists of more than 1 patch.

Further, if a patch ID in the patch groups file does not exist in the database
of the Patchwork instance, that patch ID will be silently ignored while forming
the relations.

Running this script will remove all existing relations and replace them with
the relations found in the file.

.. option:: infile

    input patch groups file.

rehash
~~~~~~

.. program:: manage.py rehash

Update the hashes on existing patches.

.. code-block:: shell

   ./manage.py rehash [<patch_id>, ...]

Patchwork stores hashes for each patch it receives. These hashes can be used to
uniquely identify a patch for things like :ref:`automatically changing the
state of the patch in Patchwork when it merges <deployment-vcs>`. If you change
your hashing algorithm, you may wish to rehash the patches.

.. option:: patch_id

   a patch ID number. If not supplied, all patches will be updated.

retag
~~~~~

.. program:: manage.py retag

Update the tag (Ack/Review/Test) counts on existing patches.

.. code-block:: shell

   ./manage.py retag [<patch_id>...]

Patchwork extracts :ref:`tags <overview-tags>` from each patch it receives. By
default, three tags are extracted, but it's possible to change this on a
per-instance basis. Should you add additional tags, you may wish to scan older
patches for these new tags.

.. option:: patch_id

   a patch ID number. If not supplied, all patches will be updated.
