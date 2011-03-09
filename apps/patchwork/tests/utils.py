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

import os
import codecs
from patchwork.models import Project, Person, UserProfile
from django.contrib.auth.models import User

from email import message_from_file
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    # Python 2.4 compatibility
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart

# helper functions for tests
_test_mail_dir  = 'patchwork/tests/mail'
_test_patch_dir = 'patchwork/tests/patches'

class defaults(object):
    project = Project(linkname = 'test-project', name = 'Test Project')

    patch_author = 'Patch Author <patch-author@example.com>'
    patch_author_person = Person(name = 'Patch Author',
        email = 'patch-author@example.com')

    comment_author = 'Comment Author <comment-author@example.com>'

    sender = 'Test Author <test-author@example.com>'

    subject = 'Test Subject'

    patch_name = 'Test Patch'

    patch = """--- /dev/null	2011-01-01 00:00:00.000000000 +0800
+++ a	2011-01-01 00:00:00.000000000 +0800
@@ -0,0 +1 @@
+a
"""

_user_idx = 1
def create_user():
    global _user_idx
    userid = 'test-%d' % _user_idx
    email = '%s@example.com' % userid
    _user_idx += 1

    user = User.objects.create_user(userid, email, userid)
    user.save()

    profile = UserProfile(user = user)
    profile.save()

    return user

def create_maintainer(project):
    user = create_user()
    profile = user.get_profile()
    profile.maintainer_projects.add(project)
    profile.save()
    return user

def find_in_context(context, key):
    if isinstance(context, list):
        for c in context:
            v = find_in_context(c, key)
            if v is not None:
                return v
    else:
        if key in context:
            return context[key]
    return None

def read_patch(filename, encoding = None):
    file_path = os.path.join(_test_patch_dir, filename)
    if encoding is not None:
        f = codecs.open(file_path, encoding = encoding)
    else:
        f = file(file_path)

    return f.read()

def read_mail(filename, project = None):
    file_path = os.path.join(_test_mail_dir, filename)
    mail = message_from_file(open(file_path))
    if project is not None:
        mail['List-Id'] = project.listid
    return mail

def create_email(content, subject = None, sender = None, multipart = False,
        project = None, content_encoding = None):
    if subject is None:
        subject = defaults.subject
    if sender is None:
        sender = defaults.sender
    if project is None:
        project = defaults.project
    if content_encoding is None:
        content_encoding = 'us-ascii'

    if multipart:
        msg = MIMEMultipart()
        body = MIMEText(content, _subtype = 'plain',
                        _charset = content_encoding)
        msg.attach(body)
    else:
        msg = MIMEText(content, _charset = content_encoding)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['List-Id'] = project.linkname


    return msg
