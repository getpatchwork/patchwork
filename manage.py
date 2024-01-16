#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE', 'patchwork.settings.production'
    )

    import django

    if django.VERSION < (3, 2):
        raise Exception('Patchwork requires Django 3.2 or greater')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
