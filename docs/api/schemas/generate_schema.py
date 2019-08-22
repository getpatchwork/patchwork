#!/usr/bin/env python3

import os

import jinja2

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
VERSIONS = [(1, 0), (1, 1), (1, 2), None]
LATEST_VERSION = (1, 2)


def generate_schema():
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
            fh.write('\n')


if __name__ == '__main__':
    generate_schema()
