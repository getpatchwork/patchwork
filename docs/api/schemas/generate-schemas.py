#!/usr/bin/env python3

import argparse
import os
import sys

import jinja2

try:
    import openapi_spec_validator
    import yaml
except ImportError:
    openapi_spec_validator = None
    yaml = None

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
VERSIONS = [(1, 0), (1, 1), (1, 2), (1, 3), None]
LATEST_VERSION = (1, 3)


def generate_schemas():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(ROOT_DIR),
        trim_blocks=True,
        lstrip_blocks=True)
    template = env.get_template('patchwork.j2')

    for version in VERSIONS:
        version_dir = os.path.join(
            ROOT_DIR, 'v%d.%d' % version if version else 'latest')

        if not os.path.exists(version_dir):
            os.mkdir(version_dir)

        version_str = '%d.%d' % (version or LATEST_VERSION)
        version_url = '%d.%d/' % version if version else ''
        version = version or LATEST_VERSION

        with open(os.path.join(version_dir, 'patchwork.yaml'), 'wb') as fh:
            template.stream(version=version, version_str=version_str,
                            version_url=version_url).dump(fh, encoding='utf-8')
            fh.write(b'\n')

    print(f'Schemas written to {ROOT_DIR}.')


def validate_schemas():
    for version in VERSIONS:
        schema = os.path.join(
            ROOT_DIR,
            'v%d.%d' % version if version else 'latest',
            'patchwork.yaml',
        )

        with open(schema) as fh:
            spec = yaml.safe_load(fh.read())
            openapi_spec_validator.validate_spec(spec)

    print('Validation successful.')


def main():
    parser = argparse.ArgumentParser(
        description='Generate schemas from the schema template.',
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='validate the generated schemas. Requires the openapi-validator '
        'package.',
    )
    args = parser.parse_args()

    if args.validate and openapi_spec_validator is None:
        print(
            '\033[1m\033[91mERROR:\033[0m Validation requires the '
            'openapi-validator and yaml packages',
            file=sys.stderr,
        )
        sys.exit(1)

    generate_schemas()

    if args.validate:
        validate_schemas()


if __name__ == '__main__':
    main()
