# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import functools
import json
import os

from django.conf import settings
from django.test import testcases

from patchwork.tests.api import validator

if settings.ENABLE_REST_API:
    from rest_framework.test import APIClient as BaseAPIClient
    from rest_framework.test import APIRequestFactory
else:
    from django.test import Client as BaseAPIClient


# docs/api/samples
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


class APIClient(BaseAPIClient):

    def __init__(self, *args, **kwargs):
        super(APIClient, self).__init__(*args, **kwargs)
        self.factory = APIRequestFactory()

    def get(self, path, data=None, follow=False, **extra):
        validate_request = extra.pop('validate_request', True)
        validate_response = extra.pop('validate_response', True)

        request = self.factory.get(
            path, data=data, SERVER_NAME='example.com', **extra)
        response = super(APIClient, self).get(
            path, data=data, follow=follow, SERVER_NAME='example.com', **extra)

        validator.validate_data(path, request, response, validate_request,
                                validate_response)

        return response

    def post(self, path, data=None, format=None, content_type=None,
             follow=False, **extra):
        validate_request = extra.pop('validate_request', True)
        validate_response = extra.pop('validate_response', True)

        request = self.factory.post(
            path, data=data, format='json', content_type=content_type,
            SERVER_NAME='example.com', **extra)
        response = super(APIClient, self).post(
            path, data=data, format='json', content_type=content_type,
            follow=follow, SERVER_NAME='example.com', **extra)

        validator.validate_data(path, request, response, validate_request,
                                validate_response)

        return response

    def put(self, path, data=None, format=None, content_type=None,
            follow=False, **extra):
        validate_request = extra.pop('validate_request', True)
        validate_response = extra.pop('validate_response', True)

        request = self.factory.put(
            path, data=data, format='json', content_type=content_type,
            SERVER_NAME='example.com', **extra)
        response = super(APIClient, self).put(
            path, data=data, format='json', content_type=content_type,
            follow=follow, SERVER_NAME='example.com', **extra)

        validator.validate_data(path, request, response, validate_request,
                                validate_response)

        return response

    def patch(self, path, data=None, format=None, content_type=None,
              follow=False, **extra):
        validate_request = extra.pop('validate_request', True)
        validate_response = extra.pop('validate_response', True)

        request = self.factory.patch(
            path, data=data, format='json', content_type=content_type,
            SERVER_NAME='example.com', **extra)
        response = super(APIClient, self).patch(
            path, data=data, format='json', content_type=content_type,
            follow=follow, SERVER_NAME='example.com', **extra)

        validator.validate_data(path, request, response, validate_request,
                                validate_response)

        return response


class APITestCase(testcases.TestCase):
    client_class = APIClient
