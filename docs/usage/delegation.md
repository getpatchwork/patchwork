# Autodelegation

Autodelegation allows patches to be automatically delegated to a user based on
the files modified by the patch. To do this, a number of rules can be
configured in the project admininstration page. This can usually be found at
`/admin/patchwork/project/<project_id>/change`.

**NOTE:** Autodelegation can only be configured by Patchwork administrators,
i.e. those that can access the 'admin' panel. If you require configuration of
autodelegation rules on a local instance, contact your Patchwork administrator.

In this section there are the following fields:

<dl>
  <dt>Path</dt>
  <dd>A path in <a href="https://docs.python.org/2/library/fnmatch.html">
  fnmatch</a> format. The fnmatch library allows for limited, Unix shell-style
  wildcarding</dd>
  <dt>User</dt>
  <dd>The patchwork user that should be autodelegated to the patch</dd>
  <dt>Priority</dt>
  <dd>The priority of the rule relative to other patches. Higher values
  indicate higher priority</dd>
</dl>

Rules should be configured by setting the above fields and saving the rules.
These rules will be applied at patch parse time.
