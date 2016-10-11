# Hint Headers

Patchwork provides a number of special email headers to control how a patch is
handled when it is received. The examples provided below use `git-send-email`,
but custom headers can also be set when using tools like `mutt`.

## `X-Patchwork-Ignore`

Valid values: *

When set, the mere presence of this header will ensure the provided email is
not parsed by Patchwork. For example:

    $ git send-email --add-header="X-Patchwork-Ignore: test" master

## `X-Patchwork-Delegate`

Valid values: An email address associated with a Patchwork user

If set and valid, the user corresponding to the provided email address will be
assigned as the delegate of any patch parsed. If invalid, it will be ignored.
For example:

    $ git send-email --add-header="X-Patchwork-Delegate: a@example.com" master

## `X-Patchwork-State`

Valid values: Varies between deployments. This can usually be one of
"Accepted", "Rejected", "RFC" or "Awaiting Upstream", among others.

If set and valid, the state provided will be assigned as the state of any patch
parsed. If invalid, it will be ignored. For example:

    $ git send-email --add-header="X-Patchwork-State: RFC" master
