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

import unittest
import os
from email import message_from_string
from patchwork.models import Project, Person

try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    # Python 2.4 compatibility
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart

test_mail_dir  = 'patchwork/tests/mail'
test_patch_dir = 'patchwork/tests/patches'

class PatchTest(unittest.TestCase):
    default_sender = 'Test Author <test@exmaple.com>'
    default_subject = 'Test Subject'
    project = Project(linkname = 'test-project')

    def create_email(self, content, subject = None, sender = None,
            multipart = False):
        if subject is None:
            subject = self.default_subject
        if sender is None:
            sender = self.default_sender

        if multipart:
            msg = MIMEMultipart()
            body = MIMEText(content, _subtype = 'plain')
            msg.attach(body)
        else:
            msg = MIMEText(content)

        msg['Subject'] = subject
        msg['From'] = sender
        msg['List-Id'] = self.project.linkname

        return msg

    def read_patch(self, filename):
        return file(os.path.join(test_patch_dir, filename)).read()


from patchwork.bin.parsemail import find_content, find_author

class InlinePatchTest(PatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test for attached patch'

    def setUp(self):
        self.orig_patch = self.read_patch(self.patch_filename)
        email = self.create_email(self.test_comment + '\n' + self.orig_patch)
        (self.patch, self.comment) = find_content(self.project, email)

    def testPatchPresence(self):
        self.assertTrue(self.patch is not None)

    def testPatchContent(self):
        self.assertEquals(self.patch.content, self.orig_patch)

    def testCommentPresence(self):
        self.assertTrue(self.comment is not None)

    def testCommentContent(self):
        self.assertEquals(self.comment.content, self.test_comment)


class AttachmentPatchTest(InlinePatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test for attached patch'

    def setUp(self):
        self.orig_patch = self.read_patch(self.patch_filename)
        email = self.create_email(self.test_comment, multipart = True)
        attachment = MIMEText(self.orig_patch, _subtype = 'x-patch')
        email.attach(attachment)
        (self.patch, self.comment) = find_content(self.project, email)


class SignatureCommentTest(InlinePatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment'

    def setUp(self):
        self.orig_patch = self.read_patch(self.patch_filename)
        email = self.create_email( \
                self.test_comment + '\n' + \
                '-- \nsig\n' + self.orig_patch)
        (self.patch, self.comment) = find_content(self.project, email)


class ListFooterTest(InlinePatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment'

    def setUp(self):
        self.orig_patch = self.read_patch(self.patch_filename)
        email = self.create_email( \
                self.test_comment + '\n' + \
                '_______________________________________________\n' + \
                'Linuxppc-dev mailing list\n' + \
                self.orig_patch)
        (self.patch, self.comment) = find_content(self.project, email)


class UpdateCommentTest(InlinePatchTest):
    """ Test for '---\nUpdate: v2' style comments to patches. """
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment\n---\nUpdate: test update'

class UpdateSigCommentTest(SignatureCommentTest):
    """ Test for '---\nUpdate: v2' style comments to patches, with a sig """
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment\n---\nUpdate: test update'

class SenderEncodingTest(unittest.TestCase):
    sender_name = u'example user'
    sender_email = 'user@example.com'
    from_header = 'example user <user@example.com>'

    def setUp(self):
        mail = 'From: %s\n' % self.from_header + \
               'Subject: test\n\n' + \
               'test'
        self.email = message_from_string(mail)
        (self.person, new) = find_author(self.email)
        self.person.save()

    def tearDown(self):
        self.person.delete()

    def testName(self):
        self.assertEquals(self.person.name, self.sender_name)

    def testEmail(self):
        self.assertEquals(self.person.email, self.sender_email)

    def testDBQueryName(self):
        db_person = Person.objects.get(name = self.sender_name)
        self.assertEquals(self.person, db_person)

    def testDBQueryEmail(self):
        db_person = Person.objects.get(email = self.sender_email)
        self.assertEquals(self.person, db_person)


class SenderUTF8QPEncodingTest(SenderEncodingTest):
    sender_name = u'\xe9xample user'
    from_header = '=?utf-8?q?=C3=A9xample=20user?= <user@example.com>'

class SenderUTF8QPSplitEncodingTest(SenderEncodingTest):
    sender_name = u'\xe9xample user'
    from_header = '=?utf-8?q?=C3=A9xample=20?= user <user@example.com>'

class SenderUTF8B64EncodingTest(SenderUTF8QPEncodingTest):
    from_header = '=?utf-8?B?w6l4YW1wbGUgdXNlcg==?= <user@example.com>'
