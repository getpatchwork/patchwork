# Autodelegation

Autodelegation allows patches to be automatically delegated to a user based on
the files modified by the patch. To do this, a number of rules can be
configured in the project administration page. This can usually be found at
`/admin/patchwork/project/<project_id>/change`.

**NOTE:** Autodelegation can only be configured by Patchwork administrators,
i.e. those that can access the 'admin' panel. If you require configuration of
autodelegation rules on a local instance, contact your Patchwork administrator.

In this section there are the following fields:

- User

    The patchwork user that should be autodelegated to the patch

- Priority

    The priority of the rule relative to other patches. Higher values indicate
    higher priority. If two rules have the same priority, ordering will be
    based on the path.

- Path

    A path in [fnmatch](https://docs.python.org/2/library/fnmatch.html) format.
    The fnmatch library allows for limited, Unix shell-style wildcarding.
    Filenames are extracted from patch lines beginning with `--- ` or `+++ `.
    Note that for projects using Git or Mercurial, the tools these VCS provide
    for producing patches are prefixed with `a` or `b`. You should account for
    this in your path. For example, to match the path `patchwork/views`
    (relative to the top of a Git repo) your pattern should be:

        ?/patchwork/views/*

    It is also possible to use relative paths, such as:

        */manage.py

    For projects using other VCSs like Subversion can simply use a bare path:

       patchwork/views/*

Rules are configured by setting the above fields and saving the rules. These
rules will be applied at patch parse time.
