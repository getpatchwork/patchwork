# Patchwork - automated patch tracking system
# Copyright (C) 2018 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import re

from django.urls import resolve
import jsonschema_path
from openapi_core.contrib.django import DjangoOpenAPIRequest
from openapi_core.contrib.django import DjangoOpenAPIResponse
from openapi_core.exceptions import OpenAPIError
from openapi_core.templating import util
from openapi_core.validation.request.exceptions import SecurityValidationError
from openapi_core import shortcuts
from rest_framework import status
import yaml

# docs/api/schemas
SCHEMAS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir,
    os.pardir,
    os.pardir,
    'docs',
    'api',
    'schemas',
)

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


EXTRA_FORMAT_VALIDATORS = {
    'uri': RegexValidator(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # noqa: E501
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
    ),
    'iso8601': RegexValidator(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}$'),
    'email': RegexValidator(r'[^@]+@[^@]+\.[^@]+'),
}


def _load_spec(version):
    global _LOADED_SPECS

    if _LOADED_SPECS.get(version):
        return _LOADED_SPECS[version]

    spec_path = os.path.join(
        SCHEMAS_DIR,
        'v{}'.format(version) if version else 'latest',
        'patchwork.yaml',
    )

    with open(spec_path, 'r') as fh:
        data = yaml.load(fh, Loader=yaml.SafeLoader)

    _LOADED_SPECS[version] = jsonschema_path.SchemaPath.from_dict(data)

    return _LOADED_SPECS[version]


def validate_data(
    path,
    request,
    response,
    validate_request,
    validate_response,
):
    if response.status_code in (
        # status.HTTP_403_FORBIDDEN,
        status.HTTP_405_METHOD_NOT_ALLOWED,
    ):
        return

    # FIXME: this shouldn't matter
    request.path = request.path.rstrip('/')

    spec = _load_spec(resolve(path).kwargs.get('version'))
    request = DjangoOpenAPIRequest(request)
    response = DjangoOpenAPIResponse(response)

    # request
    if validate_request:
        try:
            shortcuts.validate_request(
                request,
                spec=spec,
                extra_format_validators=EXTRA_FORMAT_VALIDATORS,
            )
        except SecurityValidationError:
            assert response.status_code in (
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            )
        except OpenAPIError:
            # TODO(stephenfin): In API v2.0, this should be an error. As things
            # stand, we silently ignore these issues.
            assert response.status_code == status.HTTP_200_OK

    # response
    if validate_response:
        shortcuts.validate_response(
            request,
            response,
            spec=spec,
            extra_format_validators=EXTRA_FORMAT_VALIDATORS,
        )
