Hint Headers
============

Patchwork provides a number of special email headers to control how a patch is
handled when it is received. The examples provided below use `git-send-email`,
but custom headers can also be set when using tools like `mutt`.

``X-Patchwork-Hint``
  Valid values: ignore

  When set, this header will ensure the provided email is not parsed
  by Patchwork. For example:

  .. code-block:: shell

     $ git send-email --add-header="X-Patchwork-Hint: ignore" master

``X-Patchwork-Delegate``
  Valid values: An email address associated with a Patchwork user

  If set and valid, the user corresponding to the provided email address will
  be assigned as the delegate of any patch parsed. If invalid, it will be
  ignored.  For example:

  .. code-block:: shell

     $ git send-email --add-header="X-Patchwork-Delegate: a@example.com" master

``X-Patchwork-State``
  Valid values: Varies between deployments. This can usually be one of
  "Accepted", "Rejected", "RFC" or "Awaiting Upstream", among others.

  If set and valid, the state provided will be assigned as the state of any
  patch parsed. If invalid, it will be ignored. For example:

  .. code-block:: shell

     $ git send-email --add-header="X-Patchwork-State: RFC" master

``X-Patchwork-Action-Required``
  Valid values: <none, value is ignored>

  When set on a reply to an existing cover letter or patch, this header will
  mark the comment as "unaddressed". The comment can then be addressed using
  the API or web UI. For more details, refer to
  :ref:`overview-comment-metadata`.
