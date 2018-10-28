# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import functools
import json
import os

# docs/examples
OUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
    os.pardir, 'docs', 'api', 'samples')

_WRITTEN_FILES = {}


def _duplicate_sample(filename, func):
    global _WRITTEN_FILES

    # sanity check to make sure we're not writing to the same file
    # twice
    if filename in _WRITTEN_FILES:
        # though if tests do this, we simply ignore subsequent
        # writes
        if _WRITTEN_FILES[filename] == func:
            return True

        raise Exception(
            "Tests '{}' and '{}' write to the same file".format(
                _WRITTEN_FILES[filename], func))

    _WRITTEN_FILES[filename] = func

    return False


def store_samples(filename):
    """Wrapper to store responses and requests generated in tests.

    These can be used in documentation. Only the first response or request body
    is saved per test.
    """

    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    def inner(func):

        def wrapper(self, *args, **kwargs):

            def client_wrapper(orig_func, path, data=None, *orig_args,
                               **orig_kwargs):

                req_filename = filename + '-req.json'
                resp_filename = filename + '-resp.json'

                # we don't have a request body for GET requests
                if orig_func != _get and not _duplicate_sample(
                        req_filename, func):
                    with open(os.path.join(OUT_DIR, req_filename), 'w') as fh:
                        json.dump(data, fh, indent=4, separators=(',', ': '))

                resp = orig_func(path, data, *orig_args, **orig_kwargs)

                if not _duplicate_sample(resp_filename, func):
                    with open(os.path.join(OUT_DIR, resp_filename), 'w') as fh:
                        json.dump(resp.data, fh, indent=4,
                                  separators=(',', ': '))

                return resp

            # replace client.* with our own implementations
            _get = self.client.get
            self.client.get = functools.partial(client_wrapper, _get)
            _post = self.client.post
            self.client.post = functools.partial(client_wrapper, _post)
            _put = self.client.put
            self.client.put = functools.partial(client_wrapper, _put)
            _patch = self.client.patch
            self.client.patch = functools.partial(client_wrapper, _patch)

            func(self, *args, **kwargs)

            # ...then reverse
            self.client.patch = _patch
            self.client.put = _put
            self.client.post = _post
            self.client.get = _get

        return wrapper

    return inner
