Autodelegation
==============

Autodelegation allows patches to be automatically delegated to a user based on
the files modified by the patch. To do this, a number of rules can be
configured in the project administration page. This can usually be found at:

    /admin/patchwork/project/<project_id>/change

.. note::

   Autodelegation can only be configured by Patchwork administrators, i.e.
   those that can access the 'admin' panel. If you require configuration of
   autodelegation rules on a local instance, contact your Patchwork
   administrator.

In this section there are the following fields:

User
  The patchwork user that should be autodelegated to the patch

Priority
  The priority of the rule relative to other patches. Higher values indicate
  higher priority. If two rules have the same priority, ordering will be based
  on the path.

Path
  A path in `fnmatch`__ format. The fnmatch library allows for limited, Unix
  shell-style wildcarding. Filenames are extracted from patch lines beginning
  with ``---`` or ``+++``.

  You can simply use a bare path::

      patchwork/views/about.py

  Or it is also possible to use relative paths, such as::

      */manage.py


Rules are configured by setting the above fields and saving the rules. These
rules will be applied at patch parse time.

__ https://docs.python.org/2/library/fnmatch.html
