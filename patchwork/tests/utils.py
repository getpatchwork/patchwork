# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import codecs
from datetime import datetime as dt
from datetime import timedelta
from email.utils import make_msgid
import os

from django.contrib.auth.models import User

from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Cover
from patchwork.models import CoverComment
from patchwork.models import Patch
from patchwork.models import PatchComment
from patchwork.models import PatchRelation
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import SeriesReference
from patchwork.models import State
from patchwork.tests import TEST_PATCH_DIR

SAMPLE_DIFF = """--- /dev/null\t2011-01-01 00:00:00.000000000 +0800
+++ a\t2011-01-01 00:00:00.000000000 +0800
@@ -0,0 +1 @@
+a
"""
SAMPLE_CONTENT = 'Hello, world.'


def read_patch(filename, encoding=None):
    """Read a diff from a file."""
    file_path = os.path.join(TEST_PATCH_DIR, filename)
    if encoding is not None:
        f = codecs.open(file_path, encoding=encoding)
    else:
        f = open(file_path)

    result = f.read()
    f.close()
    return result


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
        'listemail': 'test%d@example.com' % num,
        'subject_match': '',
        'list_archive_url': 'https://lists.example.com/',
        'list_archive_url_format': 'https://lists.example.com/mail/{}',
    }
    values.update(kwargs)

    return Project.objects.create(**values)


def create_person(**kwargs):
    """Create a 'Person' object."""
    num = Person.objects.count()

    values = {
        'email': 'test_person_%d@example.com' % num,
        'name': 'test_person_%d' % num,
        'user': None,
    }
    values.update(kwargs)

    return Person.objects.create(**values)


def create_user(link_person=True, **kwargs):
    """Create a 'User' object.

    Args:
        link_person (bool): If true, create a linked Person object.
    """
    num = User.objects.count()

    values = {
        'username': 'test_user_%d' % num,
        'email': 'test_user_%d@example.com' % num,
        'first_name': 'Tester',
        'last_name': 'Num%d' % num,
    }
    values.update(kwargs)

    # this one must be done rather specifically
    user = User.objects.create_user(values['username'], values['email'],
                                    values['username'],
                                    first_name=values['first_name'],
                                    last_name=values['last_name'])

    if link_person:
        # unfortunately we don't split on these
        values['name'] = ' '.join([values.pop('first_name'),
                                   values.pop('last_name')])
        values.pop('username')
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


def create_state(**kwargs):
    """Create 'State' object."""
    num = State.objects.count()

    values = {
        'name': 'state_%d' % num,
        'slug': 'state-%d' % num,
        'ordering': num,
        'action_required': True,
    }
    values.update(kwargs)

    return State.objects.create(**values)


def create_bundle(**kwargs):
    """Create 'Bundle' object."""
    num = Bundle.objects.count()

    values = {
        'owner': create_user() if 'owner' not in kwargs else None,
        'project': create_project() if 'project' not in kwargs else None,
        'name': 'test_bundle_%d' % num,
    }
    values.update(kwargs)

    return Bundle.objects.create(**values)


def create_patch(**kwargs):
    """Create 'Patch' object."""
    num = Patch.objects.count()

    # NOTE(stephenfin): Even though we could simply pass 'series' into the
    # constructor, we don't as that's not what we do in the parser and not what
    # our signal handlers (for events) expect
    if 'series' in kwargs:
        series = kwargs.pop('series')
    else:
        series = create_series(project=kwargs.pop('project', create_project()))

    if 'number' in kwargs:
        number = kwargs.pop('number', None)
    elif series:
        number = series.patches.count() + 1

    # NOTE(stephenfin): We overwrite the provided project, if there is one, to
    # maintain some degree of sanity
    if series:
        kwargs['project'] = series.project

    values = {
        'submitter': create_person() if 'submitter' not in kwargs else None,
        'delegate': None,
        'project': create_project() if 'project' not in kwargs else None,
        'msgid': make_msgid(),
        'state': create_state() if 'state' not in kwargs else None,
        'name': 'testpatch%d' % num,
        'headers': '',
        'content': 'Patch testpatch%d' % num,
        'diff': SAMPLE_DIFF,
    }
    values.update(kwargs)

    patch = Patch.objects.create(**values)

    if series:
        number = number or series.patches.count() + 1
        series.add_patch(patch, number)

    return patch


def create_cover(**kwargs):
    """Create 'Cover' object."""
    num = Cover.objects.count()

    # NOTE(stephenfin): Despite first appearances, passing 'series' to the
    # 'create' function doesn't actually cause the relationship to be created.
    # This is probably a bug in Django. However, it's convenient to do so we
    # emulate that here. For more info, see [1].
    #
    # [1] https://stackoverflow.com/q/43119575/
    if 'series' in kwargs:
        series = kwargs.pop('series')
    else:
        series = create_series(project=kwargs.pop('project', create_project()))

    # NOTE(stephenfin): We overwrite the provided project, if there is one, to
    # maintain some degree of sanity
    if series:
        kwargs['project'] = series.project

    values = {
        'submitter': create_person() if 'person' not in kwargs else None,
        'project': create_project() if 'project' not in kwargs else None,
        'msgid': make_msgid(),
        'name': 'testpatch%d' % num,
        'headers': '',
        'content': 'foo',
    }
    values.update(kwargs)

    cover = Cover.objects.create(**values)

    if series:
        series.add_cover_letter(cover)

    return cover


def create_cover_comment(**kwargs):
    """Create 'CoverComment' object."""
    values = {
        'submitter': create_person() if 'submitter' not in kwargs else None,
        'cover': create_cover() if 'cover' not in kwargs else None,
        'msgid': make_msgid(),
        'content': SAMPLE_CONTENT,
    }
    values.update(kwargs)

    return CoverComment.objects.create(**values)


def create_patch_comment(**kwargs):
    """Create 'PatchComment' object."""
    values = {
        'submitter': create_person() if 'submitter' not in kwargs else None,
        'patch': create_patch() if 'patch' not in kwargs else None,
        'msgid': make_msgid(),
        'content': SAMPLE_CONTENT,
    }
    values.update(kwargs)

    return PatchComment.objects.create(**values)


def create_check(**kwargs):
    """Create 'Check' object."""
    values = {
        'patch': create_patch() if 'patch' not in kwargs else None,
        'user': create_user() if 'user' not in kwargs else None,
        'date': dt.utcnow(),
        'state': Check.STATE_SUCCESS,
        'target_url': 'http://example.com/',
        'description': '',
        'context': 'jenkins-ci',
    }
    values.update(**kwargs)

    return Check.objects.create(**values)


def create_series(**kwargs):
    """Create 'Series' object."""
    values = {
        'project': create_project() if 'project' not in kwargs else None,
        'date': dt.utcnow(),
        'submitter': create_person() if 'submitter' not in kwargs else None,
        'total': 1,
    }
    values.update(**kwargs)

    return Series.objects.create(**values)


def create_series_reference(**kwargs):
    """Create 'SeriesReference' object."""
    project = kwargs.pop('project', create_project())
    series = kwargs.pop('series', create_series(project=project))

    values = {
        'series': series,
        'project': project,
        'msgid': make_msgid(),
    }
    values.update(**kwargs)

    return SeriesReference.objects.create(**values)


def create_relation(**kwargs):
    """Create 'PatchRelation' object."""
    return PatchRelation.objects.create(**kwargs)


def _create_submissions(create_func, count=1, **kwargs):
    """Create 'count' SubmissionMixin-based objects.

    Args:
        count (int): Number of patches to create
        kwargs (dict): Overrides for various patch fields
    """
    values = {
        'project': create_project() if 'project' not in kwargs else None,
        'submitter': create_person() if 'submitter' not in kwargs else None,
    }
    values.update(kwargs)
    date = dt.utcnow()

    objects = []
    for i in range(0, count):
        obj = create_func(date=date + timedelta(minutes=i),
                          **values)
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
    values = {
        'state': create_state() if 'state' not in kwargs else None
    }
    values.update(kwargs)

    return _create_submissions(create_patch, count, **values)


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
