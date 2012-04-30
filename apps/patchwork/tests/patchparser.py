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
from patchwork.models import Project, Person, Patch, Comment, State, \
         get_default_initial_patch_state
from patchwork.tests.utils import read_patch, read_mail, create_email, \
         defaults, create_user

try:
    from email.mime.text import MIMEText
except ImportError:
    # Python 2.4 compatibility
    from email.MIMEText import MIMEText

class PatchTest(unittest.TestCase):
    default_sender = defaults.sender
    default_subject = defaults.subject
    project = defaults.project

from patchwork.bin.parsemail import find_content, find_author, find_project, \
                                    parse_mail

class InlinePatchTest(PatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test for attached patch'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename)
        email = create_email(self.test_comment + '\n' + self.orig_patch)
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
    content_subtype = 'x-patch'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename)
        email = create_email(self.test_comment, multipart = True)
        attachment = MIMEText(self.orig_patch, _subtype = self.content_subtype)
        email.attach(attachment)
        (self.patch, self.comment) = find_content(self.project, email)

class AttachmentXDiffPatchTest(AttachmentPatchTest):
    content_subtype = 'x-diff'

class UTF8InlinePatchTest(InlinePatchTest):
    patch_filename = '0002-utf-8.patch'
    patch_encoding = 'utf-8'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename, self.patch_encoding)
        email = create_email(self.test_comment + '\n' + self.orig_patch,
                             content_encoding = self.patch_encoding)
        (self.patch, self.comment) = find_content(self.project, email)

class NoCharsetInlinePatchTest(InlinePatchTest):
    """ Test mails with no content-type or content-encoding header """
    patch_filename = '0001-add-line.patch'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename)
        email = create_email(self.test_comment + '\n' + self.orig_patch)
        del email['Content-Type']
        del email['Content-Transfer-Encoding']
        (self.patch, self.comment) = find_content(self.project, email)

class SignatureCommentTest(InlinePatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename)
        email = create_email( \
                self.test_comment + '\n' + \
                '-- \nsig\n' + self.orig_patch)
        (self.patch, self.comment) = find_content(self.project, email)


class ListFooterTest(InlinePatchTest):
    patch_filename = '0001-add-line.patch'
    test_comment = 'Test comment\nmore comment'

    def setUp(self):
        self.orig_patch = read_patch(self.patch_filename)
        email = create_email( \
                self.test_comment + '\n' + \
                '_______________________________________________\n' + \
                'Linuxppc-dev mailing list\n' + \
                self.orig_patch)
        (self.patch, self.comment) = find_content(self.project, email)


class DiffWordInCommentTest(InlinePatchTest):
    test_comment = 'Lines can start with words beginning in "diff"\n' + \
                   'difficult\nDifferent'


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
    from_header = '=?utf-8?q?=C3=A9xample?= user <user@example.com>'

class SenderUTF8B64EncodingTest(SenderUTF8QPEncodingTest):
    from_header = '=?utf-8?B?w6l4YW1wbGUgdXNlcg==?= <user@example.com>'

class SubjectEncodingTest(PatchTest):
    sender = 'example user <user@example.com>'
    subject = 'test subject'
    subject_header = 'test subject'

    def setUp(self):
        mail = 'From: %s\n' % self.sender + \
               'Subject: %s\n\n' % self.subject_header + \
               'test\n\n' + defaults.patch
        self.projects = defaults.project
        self.email = message_from_string(mail)

    def testSubjectEncoding(self):
        (patch, comment) = find_content(self.project, self.email)
        self.assertEquals(patch.name, self.subject)

class SubjectUTF8QPEncodingTest(SubjectEncodingTest):
    subject = u'test s\xfcbject'
    subject_header = '=?utf-8?q?test=20s=c3=bcbject?='

class SubjectUTF8QPMultipleEncodingTest(SubjectEncodingTest):
    subject = u'test s\xfcbject'
    subject_header = 'test =?utf-8?q?s=c3=bcbject?='

class SenderCorrelationTest(unittest.TestCase):
    existing_sender = 'Existing Sender <existing@example.com>'
    non_existing_sender = 'Non-existing Sender <nonexisting@example.com>'

    def mail(self, sender):
        return message_from_string('From: %s\nSubject: Test\n\ntest\n' % sender)

    def setUp(self):
        self.existing_sender_mail = self.mail(self.existing_sender)
        self.non_existing_sender_mail = self.mail(self.non_existing_sender)
        (self.person, new) = find_author(self.existing_sender_mail)
        self.person.save()

    def testExisingSender(self):
        (person, new) = find_author(self.existing_sender_mail)
        self.assertEqual(new, False)
        self.assertEqual(person.id, self.person.id)

    def testNonExisingSender(self):
        (person, new) = find_author(self.non_existing_sender_mail)
        self.assertEqual(new, True)
        self.assertEqual(person.id, None)

    def testExistingDifferentFormat(self):
        mail = self.mail('existing@example.com')
        (person, new) = find_author(mail)
        self.assertEqual(new, False)
        self.assertEqual(person.id, self.person.id)

    def testExistingDifferentCase(self):
        mail = self.mail(self.existing_sender.upper())
        (person, new) = find_author(mail)
        self.assertEqual(new, False)
        self.assertEqual(person.id, self.person.id)

    def tearDown(self):
        self.person.delete()

class MultipleProjectPatchTest(unittest.TestCase):
    """ Test that patches sent to multiple patchwork projects are
        handled correctly """

    test_comment = 'Test Comment'
    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'

    def setUp(self):
        self.p1 = Project(linkname = 'test-project-1', name = 'Project 1',
                listid = '1.example.com', listemail='1@example.com')
        self.p2 = Project(linkname = 'test-project-2', name = 'Project 2',
                listid = '2.example.com', listemail='2@example.com')

        self.p1.save()
        self.p2.save()

        patch = read_patch(self.patch_filename)
        email = create_email(self.test_comment + '\n' + patch)
        email['Message-Id'] = self.msgid

        del email['List-ID']
        email['List-ID'] = '<' + self.p1.listid + '>'
        parse_mail(email)

        del email['List-ID']
        email['List-ID'] = '<' + self.p2.listid + '>'
        parse_mail(email)

    def testParsedProjects(self):
        self.assertEquals(Patch.objects.filter(project = self.p1).count(), 1)
        self.assertEquals(Patch.objects.filter(project = self.p2).count(), 1)

    def tearDown(self):
        self.p1.delete()
        self.p2.delete()


class MultipleProjectPatchCommentTest(MultipleProjectPatchTest):
    """ Test that followups to multiple-project patches end up on the
        correct patch """

    comment_msgid = '<2@example.com>'
    comment_content = 'test comment'

    def setUp(self):
        super(MultipleProjectPatchCommentTest, self).setUp()

        for project in [self.p1, self.p2]:
            email = MIMEText(self.comment_content)
            email['From'] = defaults.sender
            email['Subject'] = defaults.subject
            email['Message-Id'] = self.comment_msgid
            email['List-ID'] = '<' + project.listid + '>'
            email['In-Reply-To'] = self.msgid
            parse_mail(email)

    def testParsedComment(self):
        for project in [self.p1, self.p2]:
            patch = Patch.objects.filter(project = project)[0]
            # we should see two comments now - the original mail with the patch,
            # and the one we parsed in setUp()
            self.assertEquals(Comment.objects.filter(patch = patch).count(), 2)

class ListIdHeaderTest(unittest.TestCase):
    """ Test that we parse List-Id headers from mails correctly """
    def setUp(self):
        self.project = Project(linkname = 'test-project-1', name = 'Project 1',
                listid = '1.example.com', listemail='1@example.com')
        self.project.save()

    def testNoListId(self):
        email = MIMEText('')
        project = find_project(email)
        self.assertEquals(project, None)

    def testBlankListId(self):
        email = MIMEText('')
        email['List-Id'] = ''
        project = find_project(email)
        self.assertEquals(project, None)

    def testWhitespaceListId(self):
        email = MIMEText('')
        email['List-Id'] = ' '
        project = find_project(email)
        self.assertEquals(project, None)

    def testSubstringListId(self):
        email = MIMEText('')
        email['List-Id'] = 'example.com'
        project = find_project(email)
        self.assertEquals(project, None)

    def testShortListId(self):
        """ Some mailing lists have List-Id headers in short formats, where it
            is only the list ID itself (without enclosing angle-brackets). """
        email = MIMEText('')
        email['List-Id'] = self.project.listid
        project = find_project(email)
        self.assertEquals(project, self.project)

    def testLongListId(self):
        email = MIMEText('')
        email['List-Id'] = 'Test text <%s>' % self.project.listid
        project = find_project(email)
        self.assertEquals(project, self.project)

    def tearDown(self):
        self.project.delete()

class MBoxPatchTest(PatchTest):
    def setUp(self):
        self.mail = read_mail(self.mail_file, project = self.project)

class GitPullTest(MBoxPatchTest):
    mail_file = '0001-git-pull-request.mbox'

    def testGitPullRequest(self):
        (patch, comment) = find_content(self.project, self.mail)
        self.assertTrue(patch is not None)
        self.assertTrue(patch.pull_url is not None)
        self.assertTrue(patch.content is None)
        self.assertTrue(comment is not None)

class GitPullWrappedTest(GitPullTest):
    mail_file = '0002-git-pull-request-wrapped.mbox'

class GitPullWithDiffTest(MBoxPatchTest):
    mail_file = '0003-git-pull-request-with-diff.mbox'

    def testGitPullWithDiff(self):
        (patch, comment) = find_content(self.project, self.mail)
        self.assertTrue(patch is not None)
        self.assertEqual('git://git.kernel.org/pub/scm/linux/kernel/git/tip/' +
             'linux-2.6-tip.git x86-fixes-for-linus', patch.pull_url)
        self.assertTrue(
            patch.content.startswith('diff --git a/arch/x86/include/asm/smp.h'),
            patch.content)
        self.assertTrue(comment is not None)

class GitPullGitSSHUrlTest(GitPullTest):
    mail_file = '0004-git-pull-request-git+ssh.mbox'

class GitPullSSHUrlTest(GitPullTest):
    mail_file = '0005-git-pull-request-ssh.mbox'

class GitPullHTTPUrlTest(GitPullTest):
    mail_file = '0006-git-pull-request-http.mbox'

class CVSFormatPatchTest(MBoxPatchTest):
    mail_file = '0007-cvs-format-diff.mbox'

    def testPatch(self):
        (patch, comment) = find_content(self.project, self.mail)
        self.assertTrue(patch is not None)
        self.assertTrue(comment is not None)
        self.assertTrue(patch.content.startswith('Index'))

class DelegateRequestTest(unittest.TestCase):
    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'
    invalid_delegate_email = "nobody"

    def setUp(self):
        self.patch = read_patch(self.patch_filename)
        self.user = create_user()
        self.p1 = Project(linkname = 'test-project-1', name = 'Project 1',
                listid = '1.example.com', listemail='1@example.com')
        self.p1.save()

    def get_email(self):
        email = create_email(self.patch)
        del email['List-ID']
        email['List-ID'] = '<' + self.p1.listid + '>'
        email['Message-Id'] = self.msgid
        return email

    def _assertDelegate(self, delegate):
        query = Patch.objects.filter(project=self.p1)
        self.assertEquals(query.count(), 1)
        self.assertEquals(query[0].delegate, delegate)

    def testDelegate(self):
        email = self.get_email()
        email['X-Patchwork-Delegate'] = self.user.email
        parse_mail(email)
        self._assertDelegate(self.user)

    def testNoDelegate(self):
        email = self.get_email()
        parse_mail(email)
        self._assertDelegate(None)

    def testInvalidDelegateFallsBackToNoDelegate(self):
        email = self.get_email()
        email['X-Patchwork-Delegate'] = self.invalid_delegate_email
        parse_mail(email)
        self._assertDelegate(None)

    def tearDown(self):
        self.p1.delete()
        self.user.delete()

class InitialPatchStateTest(unittest.TestCase):
    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'
    invalid_state_name = "Nonexistent Test State"

    def setUp(self):
        self.patch = read_patch(self.patch_filename)
        self.user = create_user()
        self.p1 = Project(linkname = 'test-project-1', name = 'Project 1',
                listid = '1.example.com', listemail='1@example.com')
        self.p1.save()
        self.default_state = get_default_initial_patch_state()
        self.nondefault_state = State.objects.get(name="Accepted")

    def get_email(self):
        email = create_email(self.patch)
        del email['List-ID']
        email['List-ID'] = '<' + self.p1.listid + '>'
        email['Message-Id'] = self.msgid
        return email

    def _assertState(self, state):
        query = Patch.objects.filter(project=self.p1)
        self.assertEquals(query.count(), 1)
        self.assertEquals(query[0].state, state)

    def testNonDefaultStateIsActuallyNotTheDefaultState(self):
        self.assertNotEqual(self.default_state, self.nondefault_state)

    def testExplicitNonDefaultStateRequest(self):
        email = self.get_email()
        email['X-Patchwork-State'] = self.nondefault_state.name
        parse_mail(email)
        self._assertState(self.nondefault_state)

    def testExplicitDefaultStateRequest(self):
        email = self.get_email()
        email['X-Patchwork-State'] = self.default_state.name
        parse_mail(email)
        self._assertState(self.default_state)

    def testImplicitDefaultStateRequest(self):
        email = self.get_email()
        parse_mail(email)
        self._assertState(self.default_state)

    def testInvalidTestStateDoesNotExist(self):
        with self.assertRaises(State.DoesNotExist):
            State.objects.get(name=self.invalid_state_name)

    def testInvalidStateRequestFallsBackToDefaultState(self):
        email = self.get_email()
        email['X-Patchwork-State'] = self.invalid_state_name
        parse_mail(email)
        self._assertState(self.default_state)

    def tearDown(self):
        self.p1.delete()
        self.user.delete()
