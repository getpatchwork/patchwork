# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import re

from django.urls import resolve
import openapi_core
from openapi_core.contrib.django import DjangoOpenAPIRequestFactory
from openapi_core.contrib.django import DjangoOpenAPIResponseFactory
from openapi_core.exceptions import OpenAPIParameterError
from openapi_core.templating import util
from openapi_core.unmarshalling.schemas.formatters import Formatter
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from rest_framework import status
import yaml

# docs/api/schemas
SCHEMAS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
    os.pardir, 'docs', 'api', 'schemas')

_LOADED_SPECS = {}


# HACK! Workaround for https://github.com/p1c2u/openapi-core/issues/226
def search(path_pattern, full_url_pattern):
    p = util.Parser(path_pattern)
    p._expression = p._expression + '$'
    result = p.search(full_url_pattern)
    if not result or any('/' in arg for arg in result.named.values()):
        return None

    return result


util.search = search


class RegexValidator(object):

    def __init__(self, regex):
        self.regex = re.compile(regex, re.IGNORECASE)

    def __call__(self, value):
        if not isinstance(value, str):
            return False

        if not value:
            return True

        return self.regex.match(value)


CUSTOM_FORMATTERS = {
    'uri': Formatter.from_callables(
        RegexValidator(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # noqa: E501
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
        ),
        str,
    ),
    'iso8601': Formatter.from_callables(
        RegexValidator(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}$'),
        str,
    ),
    'email': Formatter.from_callables(
        RegexValidator(r'[^@]+@[^@]+\.[^@]+'),
        str,
    ),
}


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


def validate_data(path, request, response, validate_request,
                  validate_response):
    if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return

    spec = _load_spec(resolve(path).kwargs.get('version'))
    request = DjangoOpenAPIRequestFactory.create(request)
    response = DjangoOpenAPIResponseFactory.create(response)

    # request
    if validate_request:
        validator = RequestValidator(
            spec, custom_formatters=CUSTOM_FORMATTERS)
        result = validator.validate(request)
        try:
            result.raise_for_errors()
        except OpenAPIParameterError:
            # TODO(stephenfin): In API v2.0, this should be an error. As things
            # stand, we silently ignore these issues.
            assert response.status_code == status.HTTP_200_OK

    # response
    if validate_response:
        validator = ResponseValidator(
            spec, custom_formatters=CUSTOM_FORMATTERS)
        result = validator.validate(request, response)
        result.raise_for_errors()
