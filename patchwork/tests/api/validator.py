# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import re

import django
from django.urls import resolve
from django.urls.resolvers import get_resolver
from django.utils import six
import openapi_core
from openapi_core.schema.schemas.models import Format
from openapi_core.wrappers.base import BaseOpenAPIResponse
from openapi_core.wrappers.base import BaseOpenAPIRequest
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from openapi_core.schema.parameters.exceptions import OpenAPIParameterError
from openapi_core.schema.media_types.exceptions import OpenAPIMediaTypeError
from rest_framework import status
import yaml

# docs/api/schemas
SCHEMAS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
    os.pardir, 'docs', 'api', 'schemas')

HEADER_REGEXES = (
    re.compile(r'^HTTP_.+$'), re.compile(r'^CONTENT_TYPE$'),
    re.compile(r'^CONTENT_LENGTH$'))

_LOADED_SPECS = {}


class RegexValidator(object):

    def __init__(self, regex):
        self.regex = re.compile(regex, re.IGNORECASE)

    def __call__(self, value):
        if not isinstance(value, six.text_type):
            return False

        if not value:
            return True

        return self.regex.match(value)


CUSTOM_FORMATTERS = {
    'uri': Format(six.text_type, RegexValidator(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # noqa
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$')),
    'iso8601': Format(six.text_type, RegexValidator(
        r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}$')),
    'email': Format(six.text_type, RegexValidator(
        r'[^@]+@[^@]+\.[^@]+')),
}


def _extract_headers(request):
    request_headers = {}
    for header in request.META:
        for regex in HEADER_REGEXES:
            if regex.match(header):
                request_headers[header] = request.META[header]

    return request_headers


def _resolve_django1x(path, resolver=None):
    """Resolve a given path to its matching regex (Django 1.x).

    This is essentially a re-implementation of ``RegexURLResolver.resolve``
    that builds and returns the matched regex instead of the view itself.

    >>> _resolve_django1x('/api/1.0/patches/1/checks/')
    "^api/(?:(?P<version>(1.0|1.1))/)patches/(?P<patch_id>[^/]+)/checks/$"
    """
    from django.urls.resolvers import RegexURLResolver  # noqa

    resolver = resolver or get_resolver()
    match = resolver.regex.search(path)

    if not match:
        return

    if isinstance(resolver, RegexURLResolver):
        sub_path = path[match.end():]
        for sub_resolver in resolver.url_patterns:
            sub_match = _resolve_django1x(sub_path, sub_resolver)
            if not sub_match:
                continue

            kwargs = dict(match.groupdict())
            kwargs.update(sub_match[2])
            args = sub_match[1]
            if not kwargs:
                args = match.groups() + args

            regex = resolver.regex.pattern + sub_match[0].lstrip('^')

            return regex, args, kwargs
    else:  # RegexURLPattern
        kwargs = match.groupdict()
        args = () if kwargs else match.groups()
        return resolver.regex.pattern, args, kwargs


def _resolve_django2x(path, resolver=None):
    """Resolve a given path to its matching regex (Django 2.x).

    This is essentially a re-implementation of ``URLResolver.resolve`` that
    builds and returns the matched regex instead of the view itself.

    >>> _resolve_django2x('/api/1.0/patches/1/checks/')
    "^api/(?:(?P<version>(1.0|1.1))/)patches/(?P<patch_id>[^/]+)/checks/$"
    """
    from django.urls.resolvers import URLResolver  # noqa
    from django.urls.resolvers import RegexPattern  # noqa

    resolver = resolver or get_resolver()
    match = resolver.pattern.match(path)

    # we dont handle any other type of pattern at the moment
    assert isinstance(resolver.pattern, RegexPattern)

    if not match:
        return

    if isinstance(resolver, URLResolver):
        sub_path, args, kwargs = match
        for sub_resolver in resolver.url_patterns:
            sub_match = _resolve_django2x(sub_path, sub_resolver)
            if not sub_match:
                continue

            kwargs.update(sub_match[2])
            args += sub_match[1]

            regex = resolver.pattern._regex + sub_match[0].lstrip('^')

            return regex, args, kwargs
    else:
        _, args, kwargs = match
        return resolver.pattern._regex, args, kwargs


if django.VERSION < (2, 0):
    _resolve = _resolve_django1x
else:
    _resolve = _resolve_django2x


def _resolve_path_to_kwargs(path):
    """Convert a path to the kwargs used to resolve it.

    >>> resolve_path_to_kwargs('/api/1.0/patches/1/checks/')
    {"patch_id": 1}
    """
    # TODO(stephenfin): Handle definition by args
    _, _, kwargs = _resolve(path)

    results = {}
    for key, value in kwargs.items():
        if key == 'version':
            continue

        if key == 'pk':
            key = 'id'

        results[key] = value

    return results


def _resolve_path_to_template(path):
    """Convert a path to a template string.

    >>> resolve_path_to_template('/api/1.0/patches/1/checks/')
    "/api/{version}/patches/{patch_id}/checks/"
    """
    regex, _, _ = _resolve(path)
    regex = re.match(regex, path)

    result = ''
    prev_index = 0
    for index, group in enumerate(regex.groups(), 1):
        if not group:  # group didn't match anything
            continue

        result += path[prev_index:regex.start(index)]
        prev_index = regex.end(index)
        # groupindex keys by name, not index. Switch that.
        for name, index_ in regex.re.groupindex.items():
            if index_ == (index):
                # special-case version group
                if name == 'version':
                    result += group
                    break

                if name == 'pk':
                    name = 'id'

                result += '{%s}' % name
                break

    result += path[prev_index:]

    return result


def _load_spec(version):
    global _LOADED_SPECS

    if _LOADED_SPECS.get(version):
        return _LOADED_SPECS[version]

    spec_path = os.path.join(SCHEMAS_DIR,
                             'v{}'.format(version) if version else 'latest',
                             'patchwork.yaml')

    with open(spec_path, 'r') as fh:
        data = yaml.load(fh, Loader=yaml.SafeLoader)

    _LOADED_SPECS[version] = openapi_core.create_spec(data)

    return _LOADED_SPECS[version]


class DRFOpenAPIRequest(BaseOpenAPIRequest):

    def __init__(self, request):
        self.request = request

    @property
    def host_url(self):
        return self.request.get_host()

    @property
    def path(self):
        return self.request.path

    @property
    def method(self):
        return self.request.method.lower()

    @property
    def path_pattern(self):
        return _resolve_path_to_template(self.request.path_info)

    @property
    def parameters(self):
        return {
            'path': _resolve_path_to_kwargs(self.request.path_info),
            'query': self.request.GET,
            'header': _extract_headers(self.request),
            'cookie': self.request.COOKIES,
        }

    @property
    def body(self):
        return self.request.body.decode('utf-8')

    @property
    def mimetype(self):
        return self.request.content_type


class DRFOpenAPIResponse(BaseOpenAPIResponse):

    def __init__(self, response):
        self.response = response

    @property
    def data(self):
        return self.response.content.decode('utf-8')

    @property
    def status_code(self):
        return self.response.status_code

    @property
    def mimetype(self):
        # TODO(stephenfin): Why isn't this populated?
        return 'application/json'


def validate_data(path, request, response):
    if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return

    spec = _load_spec(resolve(path).kwargs.get('version'))
    request = DRFOpenAPIRequest(request)
    response = DRFOpenAPIResponse(response)

    # request
    validator = RequestValidator(spec, custom_formatters=CUSTOM_FORMATTERS)
    result = validator.validate(request)
    try:
        result.raise_for_errors()
    except OpenAPIMediaTypeError:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    except OpenAPIParameterError:
        # TODO(stephenfin): In API v2.0, this should be an error. As things
        # stand, we silently ignore these issues.
        assert response.status_code == status.HTTP_200_OK

    # response
    validator = ResponseValidator(spec, custom_formatters=CUSTOM_FORMATTERS)
    result = validator.validate(request, response)
    result.raise_for_errors()
