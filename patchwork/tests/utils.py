# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# This file is part of the Patchwork package.
#
# Patchwork is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Patchwork is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import codecs
from datetime import datetime as dt
from email.utils import make_msgid
import os

from django.contrib.auth.models import User

from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Comment
from patchwork.models import CoverLetter
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import Project

SAMPLE_DIFF = """--- /dev/null	2011-01-01 00:00:00.000000000 +0800
+++ a	2011-01-01 00:00:00.000000000 +0800
@@ -0,0 +1 @@
+a
"""
SAMPLE_CONTENT = 'Hello, world.'
TEST_PATCH_DIR = os.path.join(os.path.dirname(__file__), 'patches')


def read_patch(filename, encoding=None):
    """Read a diff from a file."""
    file_path = os.path.join(TEST_PATCH_DIR, filename)
    if encoding is not None:
        f = codecs.open(file_path, encoding=encoding)
    else:
        f = open(file_path)

    return f.read()


class defaults(object):
    project = Project(linkname='test-project', name='Test Project',
                      listid='test.example.com')

    patch_author = 'Patch Author <patch-author@example.com>'
    patch_author_person = Person(name='Patch Author',
                                 email='patch-author@example.com')

    comment_author = 'Comment Author <comment-author@example.com>'

    sender = 'Test Author <test-author@example.com>'

    subject = 'Test Subject'

    patch_name = 'Test Patch'

    patch = """--- /dev/null	2011-01-01 00:00:00.000000000 +0800
+++ a	2011-01-01 00:00:00.000000000 +0800
@@ -0,0 +1 @@
+a
"""

error_strings = {
    'email': 'Enter a valid email address.',
}


def create_project(**kwargs):
    """Create a 'Project' object."""
    num = Project.objects.count()

    values = {
        'linkname': 'test-project-%d' % num,
        'name': 'Test Project %d' % num,
        'listid': 'test%d.example.com' % num,
    }
    values.update(kwargs)

    project = Project(**values)
    project.save()

    return project


def create_person(**kwargs):
    """Create a 'Person' object."""
    num = Person.objects.count()

    values = {
        'email': 'test_person_%d@example.com' % num,
        'name': 'test_person_%d' % num,
        'user': None,
    }
    values.update(kwargs)

    person = Person(**values)
    person.save()

    return person


def create_user(link_person=True, **kwargs):
    """Create a 'User' object.

    Args:
        link_person (bool): If true, create a linked Person object.
    """
    num = User.objects.count()

    values = {
        'name': 'test_user_%d' % num,
        'email': 'test_user_%d@example.com' % num,
    }
    values.update(kwargs)

    user = User.objects.create_user(values['name'], values['email'],
                                    values['name'])
    user.save()

    if link_person:
        create_person(user=user, **values)

    return user


def create_maintainer(project=None, **kwargs):
    """Create a 'User' and set as maintainer for provided project."""
    if not project:
        project = create_project()

    user = create_user(**kwargs)

    profile = user.profile
    profile.maintainer_projects.add(project)
    profile.save()

    return user


def create_bundle(**kwargs):
    """Create 'Bundle' object."""
    num = Bundle.objects.count()

    values = {
        'owner': create_user(),
        'project': create_project(),
        'name': 'test_bundle_%d' % num,
    }
    values.update(kwargs)

    bundle = Bundle(**values)
    bundle.save()

    return bundle


def create_patch(**kwargs):
    """Create 'Patch' object."""
    num = Patch.objects.count()

    values = {
        'submitter': create_person(),
        'delegate': None,
        'project': create_project(),
        'msgid': make_msgid(),
        'name': 'testpatch%d' % num,
        'headers': '',
        'content': '',
        'diff': SAMPLE_DIFF,
    }
    values.update(kwargs)

    patch = Patch(**values)
    patch.save()

    return patch


def create_cover(**kwargs):
    """Create 'CoverLetter' object."""
    num = CoverLetter.objects.count()

    values = {
        'submitter': create_person(),
        'project': create_project(),
        'msgid': make_msgid(),
        'name': 'testpatch%d' % num,
        'headers': '',
        'content': '',
    }
    values.update(kwargs)

    cover = CoverLetter(**values)
    cover.save()

    return cover


def create_comment(**kwargs):
    """Create 'Comment' object."""
    values = {
        'submitter': create_person(),
        'submission': create_patch(),
        'msgid': make_msgid(),
        'content': SAMPLE_CONTENT,
    }
    values.update(kwargs)

    comment = Comment(**values)
    comment.save()

    return comment


def create_check(**kwargs):
    """Create 'Check' object."""
    values = {
        'patch': create_patch(),
        'user': create_user(),
        'date': dt.now(),
        'state': Check.STATE_SUCCESS,
        'target_url': 'http://example.com/',
        'description': '',
        'context': 'jenkins-ci',
    }
    values.update(**kwargs)

    check = Check(**values)
    check.save()

    return check


def _create_submissions(create_func, count=1, **kwargs):
    """Create 'count' Submission-based objects.

    Args:
        count (int): Number of patches to create
        kwargs (dict): Overrides for various patch fields
    """
    defaults.project.save()
    defaults.patch_author_person.save()

    values = {
        'project': defaults.project,
        'submitter': defaults.patch_author_person,
    }
    values.update(kwargs)

    objects = []
    for i in range(0, count):
        obj = create_func(**values)
        objects.append(obj)

    return objects


def create_patches(count=1, **kwargs):
    """Create 'count' unique patches.

    This differs from 'create_patch', in that it will ensure all
    patches have at least the same project and submitter. In addition,
    it is possible to set other fields to the same value, by passing
    them as kwargs.

    Args:
        count (int): Number of patches to create
        kwargs (dict): Overrides for various patch fields
    """
    return _create_submissions(create_patch, count, **kwargs)


def create_covers(count=1, **kwargs):
    """Create 'count' unique cover letters.

    This differs from 'create_cover', in that it will ensure all cover
    letters have at least the same project and submitter. In addition,
    it is possible to set other fields to the same value, by passing
    them as kwargs.

    Args:
        count (int): Number of cover letters to create
        kwargs (dict): Overrides for various cover letter fields
    """
    return _create_submissions(create_cover, count, **kwargs)
