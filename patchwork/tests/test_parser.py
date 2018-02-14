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

import email
from email import message_from_string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
import os
import unittest

from django.test import TestCase
from django.test import TransactionTestCase
from django.utils import six

from patchwork.models import Comment
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import State
from patchwork.parser import clean_subject
from patchwork.parser import find_author
from patchwork.parser import find_patch_content as find_content
from patchwork.parser import find_project
from patchwork.parser import find_series
from patchwork.parser import parse_mail as _parse_mail
from patchwork.parser import parse_pull_request
from patchwork.parser import parse_series_marker
from patchwork.parser import parse_version
from patchwork.parser import split_prefixes
from patchwork.parser import subject_check
from patchwork.tests import TEST_MAIL_DIR
from patchwork.tests import TEST_FUZZ_DIR
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_series_reference
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user
from patchwork.tests.utils import read_patch
from patchwork.tests.utils import SAMPLE_DIFF


def load_mail(file_path):
    if six.PY3:
        with open(file_path, 'rb') as f:
            mail = email.message_from_binary_file(f)
    else:
        with open(file_path) as f:
            mail = email.message_from_file(f)
    return mail


def read_mail(filename, project=None):
    """Read a mail from a file."""
    file_path = os.path.join(TEST_MAIL_DIR, filename)
    mail = load_mail(file_path)
    if 'Message-Id' not in mail:
        mail['Message-Id'] = make_msgid()
    if project:
        mail['List-Id'] = project.listid
    return mail


def _create_email(msg, msgid=None, sender=None, listid=None, in_reply_to=None):
    msg['Message-Id'] = msgid or make_msgid()
    msg['Subject'] = 'Test subject'
    msg['From'] = sender or 'Test Author <test-author@example.com>'
    msg['List-Id'] = listid or 'test.example.com'
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to

    return msg


def create_email(content, msgid=None, sender=None, listid=None,
                 in_reply_to=None):
    msg = MIMEText(content, _charset='us-ascii')

    return _create_email(msg, msgid, sender, listid, in_reply_to)


def parse_mail(*args, **kwargs):
    create_state()
    return _parse_mail(*args, **kwargs)


class PatchTest(TestCase):

    def _find_content(self, mbox_filename):
        mail = read_mail(mbox_filename)
        diff, message = find_content(mail)

        return diff, message


class InlinePatchTest(PatchTest):

    orig_content = 'Test for attached patch'
    orig_diff = read_patch('0001-add-line.patch')

    def setUp(self):
        email = create_email(self.orig_content + '\n' + self.orig_diff)
        self.diff, self.content = find_content(email)

    def test_patch_content(self):
        self.assertEqual(self.diff, self.orig_diff)

    def test_patch_diff(self):
        self.assertEqual(self.content, self.orig_content)


class AttachmentPatchTest(InlinePatchTest):

    orig_content = 'Test for attached patch'
    content_subtype = 'x-patch'

    def setUp(self):
        msg = MIMEMultipart()
        body = MIMEText(self.orig_content, _subtype='plain')
        attachment = MIMEText(self.orig_diff, _subtype=self.content_subtype)
        msg.attach(body)
        msg.attach(attachment)
        email = _create_email(msg)

        self.diff, self.content = find_content(email)


class AttachmentXDiffPatchTest(AttachmentPatchTest):

    content_subtype = 'x-diff'


class UTF8InlinePatchTest(InlinePatchTest):

    orig_diff = read_patch('0002-utf-8.patch', 'utf-8')

    def setUp(self):
        msg = MIMEText(self.orig_content + '\n' + self.orig_diff,
                       _charset='utf-8')
        email = _create_email(msg)

        self.diff, self.content = find_content(email)


class NoCharsetInlinePatchTest(InlinePatchTest):
    """Test mails with no content-type or content-encoding header."""

    def setUp(self):
        email = create_email(self.orig_content + '\n' + self.orig_diff)
        del email['Content-Type']
        del email['Content-Transfer-Encoding']

        self.diff, self.content = find_content(email)


class SignatureCommentTest(InlinePatchTest):

    orig_content = 'Test comment\nmore comment'

    def setUp(self):
        email = create_email(self.orig_content + '\n-- \nsig\n' +
                             self.orig_diff)

        self.diff, self.content = find_content(email)


class UpdateSigCommentTest(SignatureCommentTest):
    """Test for '---\nUpdate: v2' style comments to patches, with a sig."""

    patch_filename = '0001-add-line.patch'
    orig_content = 'Test comment\nmore comment\n---\nUpdate: test update'


class ListFooterTest(InlinePatchTest):

    orig_content = 'Test comment\nmore comment'

    def setUp(self):
        email = create_email('\n'.join([
            self.orig_content,
            '_______________________________________________',
            'Linuxppc-dev mailing list',
            self.orig_diff]))

        self.diff, self.content = find_content(email)


class DiffWordInCommentTest(InlinePatchTest):

    orig_content = 'Lines can start with words beginning in "diff"\n' + \
                   'difficult\nDifferent'


class UpdateCommentTest(InlinePatchTest):
    """Test for '---\nUpdate: v2' style comments to patches."""

    orig_content = 'Test comment\nmore comment\n---\nUpdate: test update'


class SenderEncodingTest(TestCase):
    """Validate correct handling of encoded recipients."""

    @staticmethod
    def _create_email(from_header):
        mail = 'Message-Id: %s\n' % make_msgid() + \
               'From: %s\n' % from_header + \
               'Subject: test\n\n' + \
               'test'
        return message_from_string(mail)

    def _test_encoding(self, from_header, sender_name, sender_email):
        email = self._create_email(from_header)
        person = find_author(email)
        person.save()

        # ensure it was parsed correctly
        self.assertEqual(person.name, sender_name)
        self.assertEqual(person.email, sender_email)

        # ...and that it's queryable from DB
        db_person = Person.objects.get(name=sender_name)
        self.assertEqual(person, db_person)
        db_person = Person.objects.get(email=sender_email)
        self.assertEqual(person, db_person)

    def test_empty(self):
        email = self._create_email('')
        with self.assertRaises(ValueError):
            find_author(email)

    def test_ascii_encoding(self):
        from_header = 'example user <user@example.com>'
        sender_name = u'example user'
        sender_email = 'user@example.com'
        self._test_encoding(from_header, sender_name, sender_email)

    def test_utf8qp_encoding(self):
        from_header = '=?utf-8?q?=C3=A9xample=20user?= <user@example.com>'
        sender_name = u'\xe9xample user'
        sender_email = 'user@example.com'
        self._test_encoding(from_header, sender_name, sender_email)

    def test_utf8qp_split_encoding(self):
        from_header = '=?utf-8?q?=C3=A9xample?= user <user@example.com>'
        sender_name = u'\xe9xample user'
        sender_email = 'user@example.com'
        self._test_encoding(from_header, sender_name, sender_email)

    def test_utf8b64_encoding(self):
        from_header = '=?utf-8?B?w6l4YW1wbGUgdXNlcg==?= <user@example.com>'
        sender_name = u'\xe9xample user'
        sender_email = 'user@example.com'
        self._test_encoding(from_header, sender_name, sender_email)


class SenderCorrelationTest(TestCase):
    """Validate correct behavior of the find_author case.

    Relies of checking the internal state of a Django model object.

    http://stackoverflow.com/a/19379636/613428
    """

    @staticmethod
    def _create_email(from_header):
        mail = 'Message-Id: %s\n' % make_msgid() + \
               'From: %s\n' % from_header + \
               'Subject: Tests\n\n'\
               'test\n'
        return message_from_string(mail)

    def test_non_existing_sender(self):
        sender = 'Non-existing Sender <nonexisting@example.com>'
        mail = self._create_email(sender)

        # don't create the person - attempt to find immediately
        person = find_author(mail)
        self.assertEqual(person._state.adding, True)
        self.assertEqual(person.id, None)

    def test_existing_sender(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        # create the person first
        person_a = find_author(mail)
        person_a.save()

        # then attempt to parse email with the same 'From' line
        person_b = find_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_existing_different_format(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        # create the person first
        person_a = find_author(mail)
        person_a.save()

        # then attempt to parse email with a new 'From' line
        mail = self._create_email('existing@example.com')
        person_b = find_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_existing_different_case(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        person_a = find_author(mail)
        person_a.save()

        mail = self._create_email(sender.upper())
        person_b = find_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)


class SeriesCorrelationTest(TestCase):
    """Validate correct behavior of find_series."""

    @staticmethod
    def _create_email(msgid, references=None):
        """Create a sample mail.

        Arguments:
            msgid (str): The message's msgid
            references (list): A list of preceding messages' msgids,
                oldest first
        """
        mail = 'Message-Id: %s\n' % msgid + \
               'From: example user <user@example.com>\n' + \
               'Subject: Tests\n'

        if references:
            mail += 'In-Reply-To: %s\n' % references[-1]
            mail += 'References: %s\n' % '\n\t'.join(references)

        mail += 'test\n\n' + SAMPLE_DIFF
        return message_from_string(mail)

    def test_new_series(self):
        msgid = make_msgid()
        email = self._create_email(msgid)
        project = create_project()

        self.assertIsNone(find_series(project, email))

    def test_first_reply(self):
        msgid_a = make_msgid()
        msgid_b = make_msgid()
        email = self._create_email(msgid_b, [msgid_a])

        # assume msgid_a was already handled
        ref = create_series_reference(msgid=msgid_a)

        series = find_series(ref.series.project, email)
        self.assertEqual(series, ref.series)

    def test_nested_series(self):
        """Handle a series sent in-reply-to an existing series."""
        # create an old series with a "cover letter"
        msgids = [make_msgid()]
        project = create_project()
        series_v1 = create_series(project=project)
        create_series_reference(msgid=msgids[0], series=series_v1)

        # ...and three patches
        for i in range(3):
            msgids.append(make_msgid())
            create_series_reference(msgid=msgids[-1], series=series_v1)

        # now create a new series with "cover letter"
        msgids.append(make_msgid())
        series_v2 = create_series(project=project)
        ref_v2 = create_series_reference(msgid=msgids[-1], series=series_v2)

        # ...and the "first patch" of this new series
        msgid = make_msgid()
        email = self._create_email(msgid, msgids)
        series = find_series(project, email)

        # this should link to the second series - not the first
        self.assertEqual(len(msgids), 4 + 1)  # old series + new cover
        self.assertEqual(series, ref_v2.series)


class SubjectEncodingTest(TestCase):
    """Validate correct handling of encoded subjects."""

    @staticmethod
    def _create_email(subject):
        mail = 'Message-Id: %s\n' % make_msgid() + \
               'From: example user <user@example.com>\n' + \
               'Subject: %s\n\n' % subject + \
               'test\n\n' + SAMPLE_DIFF
        return message_from_string(mail)

    def _test_encoding(self, subject_header, parsed_subject):
        email = self._create_email(subject_header)
        name, _ = clean_subject(email.get('Subject'))
        self.assertEqual(name, parsed_subject)

    def test_subject_ascii_encoding(self):
        subject_header = 'test subject'
        subject = 'test subject'
        self._test_encoding(subject_header, subject)

    def test_subject_utf8qp_encoding(self):
        subject_header = '=?utf-8?q?test=20s=c3=bcbject?='
        subject = u'test s\xfcbject'
        self._test_encoding(subject_header, subject)

    def test_subject_utf8qp_multiple_encoding(self):
        subject_header = 'test =?utf-8?q?s=c3=bcbject?='
        subject = u'test s\xfcbject'
        self._test_encoding(subject_header, subject)


class MultipleProjectPatchTest(TestCase):
    """Test that patches sent to multiple patchwork projects are
       handled correctly."""

    orig_content = 'Test Comment'
    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'

    def setUp(self):
        self.p1 = create_project()
        self.p2 = create_project()

        patch = read_patch(self.patch_filename)
        email = create_email(
            content=''.join([self.orig_content, '\n', patch]),
            msgid=self.msgid,
            listid='<%s>' % self.p1.listid)
        parse_mail(email)

        del email['List-ID']
        email['List-ID'] = '<%s>' % self.p2.listid
        parse_mail(email)

    def test_parsed_projects(self):
        self.assertEqual(Patch.objects.filter(project=self.p1).count(), 1)
        self.assertEqual(Patch.objects.filter(project=self.p2).count(), 1)


class MultipleProjectPatchCommentTest(MultipleProjectPatchTest):
    """Test that followups to multiple-project patches end up on the
       correct patch."""

    comment_msgid = '<2@example.com>'
    comment_content = 'test comment'

    def setUp(self):
        super(MultipleProjectPatchCommentTest, self).setUp()

        for project in [self.p1, self.p2]:
            email = create_email(
                content=self.comment_content,
                msgid=self.comment_msgid,
                listid='<%s>' % project.listid)
            email['In-Reply-To'] = self.msgid
            parse_mail(email)

    def test_parsed_comment(self):
        for project in [self.p1, self.p2]:
            patch = Patch.objects.filter(project=project)[0]
            # we should see the reply comment only
            self.assertEqual(
                Comment.objects.filter(submission=patch).count(), 1)


class ListIdHeaderTest(TestCase):
    """Test that we parse List-Id headers from mails correctly."""

    def setUp(self):
        self.project = create_project()

    def test_no_list_id(self):
        email = MIMEText('')
        project = find_project(email)
        self.assertEqual(project, None)

    def test_blank_list_id(self):
        email = MIMEText('')
        email['List-Id'] = ''
        project = find_project(email)
        self.assertEqual(project, None)

    def test_whitespace_list_id(self):
        email = MIMEText('')
        email['List-Id'] = ' '
        project = find_project(email)
        self.assertEqual(project, None)

    def test_substring_list_id(self):
        email = MIMEText('')
        email['List-Id'] = 'example.com'
        project = find_project(email)
        self.assertEqual(project, None)

    def test_short_list_id(self):
        """Some mailing lists have List-Id headers in short formats, where it
           is only the list ID itself (without enclosing angle-brackets). """
        email = MIMEText('')
        email['List-Id'] = self.project.listid
        project = find_project(email)
        self.assertEqual(project, self.project)

    def test_long_list_id(self):
        email = MIMEText('')
        email['List-Id'] = 'Test text <%s>' % self.project.listid
        project = find_project(email)
        self.assertEqual(project, self.project)


class PatchParseTest(PatchTest):
    """Test parsing of different patch formats."""

    def _test_pull_request_parse(self, mbox_filename):
        diff, message = self._find_content(mbox_filename)
        pull_url = parse_pull_request(message)
        self.assertTrue(diff is None)
        self.assertTrue(message is not None)
        self.assertTrue(pull_url is not None)

    def test_git_pull_request(self):
        self._test_pull_request_parse('0001-git-pull-request.mbox')

    @unittest.skipIf(six.PY3, 'Breaks only on Python 2')
    def test_git_pull_request_crlf_newlines(self):
        # verify that we haven't munged the file
        crlf_file = os.path.join(TEST_MAIL_DIR,
                                 '0018-git-pull-request-crlf-newlines.mbox')
        with open(crlf_file) as f:
            message = f.read()
            self.assertIn('\r\n', message)

        # verify the file works
        self._test_pull_request_parse(
            '0018-git-pull-request-crlf-newlines.mbox')

    def test_git_pull_wrapped_request(self):
        self._test_pull_request_parse('0002-git-pull-request-wrapped.mbox')

    def test_git_pull_git_ssh_url(self):
        self._test_pull_request_parse('0004-git-pull-request-git+ssh.mbox')

    def test_git_pull_ssh_url(self):
        self._test_pull_request_parse('0005-git-pull-request-ssh.mbox')

    def test_git_pull_http_url(self):
        self._test_pull_request_parse('0006-git-pull-request-http.mbox')

    def test_git_pull_git_2_14_3(self):
        """Handle messages from Git 2.14.3+.

        See: https://github.com/git/git/commit/e66d7c37a
        """
        self._test_pull_request_parse('0017-git-pull-request-git-2-14-3.mbox')

    def test_git_pull_with_diff(self):
        diff, message = self._find_content(
            '0003-git-pull-request-with-diff.mbox')
        pull_url = parse_pull_request(message)
        self.assertEqual(
            'git://git.kernel.org/pub/scm/linux/kernel/git/tip/'
            'linux-2.6-tip.git x86-fixes-for-linus',
            pull_url)
        self.assertTrue(
            diff.startswith('diff --git a/arch/x86/include/asm/smp.h'),
            diff)

    def test_git_rename(self):
        diff, _ = self._find_content('0008-git-rename.mbox')
        self.assertTrue(diff is not None)
        self.assertEqual(diff.count("\nrename from "), 2)
        self.assertEqual(diff.count("\nrename to "), 2)

    def test_git_rename_with_diff(self):
        diff, message = self._find_content('0009-git-rename-with-diff.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)
        self.assertEqual(diff.count("\nrename from "), 2)
        self.assertEqual(diff.count("\nrename to "), 2)
        self.assertEqual(diff.count('\n-a\n+b'), 1)

    def test_cvs_format(self):
        diff, message = self._find_content('0007-cvs-format-diff.mbox')
        self.assertTrue(diff.startswith('Index'))

    def test_invalid_charset(self):
        """Validate behavior with an invalid charset name.

        Ensure that we can parse with one of the fallback encodings.
        """
        diff, message = self._find_content('0010-invalid-charset.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)

    def test_no_newline(self):
        """Validate behavior when trailing newline is absent."""
        diff, message = self._find_content(
            '0011-no-newline-at-end-of-file.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)
        self.assertTrue(diff.startswith(
            'diff --git a/tools/testing/selftests/powerpc/Makefile'))
        # Confirm the trailing no newline marker doesn't end up in the comment
        self.assertFalse(message.rstrip().endswith(
            r'\ No newline at end of file'))
        # Confirm it's instead at the bottom of the patch
        self.assertTrue(diff.rstrip().endswith(
            r'\ No newline at end of file'))
        # Confirm we got both markers
        self.assertEqual(2, diff.count(r'\ No newline at end of file'))

    def test_no_subject(self):
        """Validate parsing a mail with no subject."""
        diff, message = self._find_content('0016-no-subject.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)


class EncodingParseTest(TestCase):
    """Test parsing of patches with different encoding issues."""

    def setUp(self):
        self.project = create_project()

    def _test_encoded_patch_parse(self, mbox_filename):
        mail = read_mail(mbox_filename, self.project)
        parse_mail(mail, list_id=self.project.listid)
        self.assertEqual(Patch.objects.all().count(), 1)

    def test_invalid_header_char(self):
        """Validate behaviour when an invalid character is in a header."""
        self._test_encoded_patch_parse('0012-invalid-header-char.mbox')

    def test_utf8_mail(self):
        """Validate behaviour when a UTF-8 char is in a message."""
        self._test_encoded_patch_parse('0013-with-utf8-body.mbox')

    def test_utf8_unencoded_headers(self):
        """Validate behaviour when unencoded UTF-8 is in headers,
        including subject and from."""
        self._test_encoded_patch_parse('0014-with-unencoded-utf8-headers.mbox')

    def test_invalid_utf8_headers(self):
        """Validate behaviour when invalid encoded UTF-8 is in headers."""
        self._test_encoded_patch_parse('0015-with-invalid-utf8-headers.mbox')


class DelegateRequestTest(TestCase):

    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'
    invalid_delegate_email = "nobody"

    def setUp(self):
        self.patch = read_patch(self.patch_filename)
        self.user = create_user()
        self.project = create_project()

    def _get_email(self):
        email = create_email(self.patch)
        del email['List-ID']
        email['List-ID'] = '<' + self.project.listid + '>'
        email['Message-Id'] = self.msgid
        return email

    def assertDelegate(self, delegate):  # noqa
        query = Patch.objects.filter(project=self.project)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query[0].delegate, delegate)

    def test_delegate(self):
        email = self._get_email()
        email['X-Patchwork-Delegate'] = self.user.email
        parse_mail(email)
        self.assertDelegate(self.user)

    def test_no_delegate(self):
        email = self._get_email()
        parse_mail(email)
        self.assertDelegate(None)

    def test_invalid_delegate(self):
        email = self._get_email()
        email['X-Patchwork-Delegate'] = self.invalid_delegate_email
        parse_mail(email)
        self.assertDelegate(None)


class InitialPatchStateTest(TestCase):

    patch_filename = '0001-add-line.patch'
    msgid = '<1@example.com>'
    invalid_state_name = "Nonexistent Test State"

    def setUp(self):
        self.default_state = create_state()
        self.nondefault_state = create_state()

        self.patch = read_patch(self.patch_filename)
        self.user = create_user()
        self.project = create_project()

    def _get_email(self):
        email = create_email(
            self.patch, msgid=self.msgid, listid='<%s>' % self.project.listid)
        return email

    def assertState(self, state):  # noqa
        query = Patch.objects.filter(project=self.project)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query[0].state, state)

    def test_non_default_state(self):
        self.assertNotEqual(self.default_state, self.nondefault_state)

    def test_explicit_non_default_state_request(self):
        email = self._get_email()
        email['X-Patchwork-State'] = self.nondefault_state.name
        parse_mail(email)
        self.assertState(self.nondefault_state)

    def test_explicit_default_state_request(self):
        email = self._get_email()
        email['X-Patchwork-State'] = self.default_state.name
        parse_mail(email)
        self.assertState(self.default_state)

    def test_implicit_default_state_request(self):
        email = self._get_email()
        parse_mail(email)
        self.assertState(self.default_state)

    def test_invalid_state(self):
        # make sure it's actually invalid
        with self.assertRaises(State.DoesNotExist):
            State.objects.get(name=self.invalid_state_name)

        email = self._get_email()
        email['X-Patchwork-State'] = self.invalid_state_name
        parse_mail(email)
        self.assertState(self.default_state)


class ParseInitialTagsTest(PatchTest):

    fixtures = ['default_tags']
    patch_filename = '0001-add-line.patch'
    orig_content = ('test comment\n\n' +
                    'Tested-by: Test User <test@example.com>\n' +
                    'Reviewed-by: Test User <test@example.com>\n')

    def setUp(self):
        project = create_project(listid='test.example.com')
        self.orig_diff = read_patch(self.patch_filename)
        email = create_email(self.orig_content + '\n' + self.orig_diff,
                             listid=project.listid)
        parse_mail(email)

    def test_tags(self):
        self.assertEqual(Patch.objects.count(), 1)
        patch = Patch.objects.all()[0]
        self.assertEqual(patch.patchtag_set.filter(
            tag__name='Acked-by').count(), 0)
        self.assertEqual(patch.patchtag_set.get(
            tag__name='Reviewed-by').count, 1)
        self.assertEqual(patch.patchtag_set.get(
            tag__name='Tested-by').count, 1)


class ParseCommentTagsTest(PatchTest):
    fixtures = ['default_tags']
    patch_filename = '0001-add-line.patch'
    comment_content = ('test comment\n\n' +
                       'Tested-by: Test User <test@example.com>\n' +
                       'Reviewed-by: Test User <test@example.com>\n')

    def setUp(self):
        project = create_project(listid='test.example.com')
        self.orig_diff = read_patch(self.patch_filename)
        email = create_email(self.orig_diff,
                             listid=project.listid)
        parse_mail(email)
        email2 = create_email(self.comment_content,
                              in_reply_to=email['Message-Id'])
        parse_mail(email2)

    def test_tags(self):
        self.assertEqual(Patch.objects.count(), 1)
        patch = Patch.objects.all()[0]
        self.assertEqual(patch.patchtag_set.filter(
            tag__name='Acked-by').count(), 0)
        self.assertEqual(patch.patchtag_set.get(
            tag__name='Reviewed-by').count, 1)
        self.assertEqual(patch.patchtag_set.get(
            tag__name='Tested-by').count, 1)


class SubjectTest(TestCase):

    def test_clean_subject(self):
        self.assertEqual(clean_subject('meep'), ('meep', []))
        self.assertEqual(clean_subject('Re: meep'), ('meep', []))
        self.assertEqual(clean_subject('[PATCH] meep'), ('meep', []))
        self.assertEqual(clean_subject("[PATCH] meep \n meep"),
                         ('meep meep', []))
        self.assertEqual(clean_subject('[PATCH RFC] meep'),
                         ('[RFC] meep', ['RFC']))
        self.assertEqual(clean_subject('[PATCH,RFC] meep'),
                         ('[RFC] meep', ['RFC']))
        self.assertEqual(clean_subject('[PATCH,1/2] meep'),
                         ('[1/2] meep', ['1/2']))
        self.assertEqual(clean_subject('[PATCH RFC 1/2] meep'),
                         ('[RFC,1/2] meep', ['RFC', '1/2']))
        self.assertEqual(clean_subject('[PATCH] [RFC] meep'),
                         ('[RFC] meep', ['RFC']))
        self.assertEqual(clean_subject('[PATCH] [RFC,1/2] meep'),
                         ('[RFC,1/2] meep', ['RFC', '1/2']))
        self.assertEqual(clean_subject('[PATCH] [RFC] [1/2] meep'),
                         ('[RFC,1/2] meep', ['RFC', '1/2']))
        self.assertEqual(clean_subject('[PATCH] rewrite [a-z] regexes'),
                         ('rewrite [a-z] regexes', []))
        self.assertEqual(clean_subject('[PATCH] [RFC] rewrite [a-z] regexes'),
                         ('[RFC] rewrite [a-z] regexes', ['RFC']))
        self.assertEqual(clean_subject('[foo] [bar] meep', ['foo']),
                         ('[bar] meep', ['bar']))
        self.assertEqual(clean_subject('[FOO] [bar] meep', ['foo']),
                         ('[bar] meep', ['bar']))

    def test_subject_check(self):
        self.assertIsNotNone(subject_check('RE: meep'))
        self.assertIsNotNone(subject_check('Re: meep'))
        self.assertIsNotNone(subject_check('re: meep'))
        self.assertIsNotNone(subject_check('RE meep'))
        self.assertIsNotNone(subject_check('Re meep'))
        self.assertIsNotNone(subject_check('re meep'))

    def test_split_prefixes(self):
        self.assertEqual(split_prefixes('PATCH'), ['PATCH'])
        self.assertEqual(split_prefixes('PATCH,RFC'), ['PATCH', 'RFC'])
        self.assertEqual(split_prefixes(''), [])
        self.assertEqual(split_prefixes('PATCH,'), ['PATCH'])
        self.assertEqual(split_prefixes('PATCH '), ['PATCH'])
        self.assertEqual(split_prefixes('PATCH,RFC'), ['PATCH', 'RFC'])
        self.assertEqual(split_prefixes('PATCH 1/2'), ['PATCH', '1/2'])

    def test_series_markers(self):
        self.assertEqual(parse_series_marker([]), (None, None))
        self.assertEqual(parse_series_marker(['bar']), (None, None))
        self.assertEqual(parse_series_marker(['bar', '1/2']), (1, 2))
        self.assertEqual(parse_series_marker(['bar', '0/12']), (0, 12))
        self.assertEqual(parse_series_marker(['bar', '1 of 2']), (1, 2))
        self.assertEqual(parse_series_marker(['bar', '0 of 12']), (0, 12))
        # Handle people missing the space between PATCH and the markers
        # e.g. PATCH1/8
        self.assertEqual(parse_series_marker(['PATCH1/8']), (1, 8))
        self.assertEqual(parse_series_marker(['PATCH1 of 8']), (1, 8))
        # verify the prefix-stripping is non-greedy
        self.assertEqual(parse_series_marker(['PATCH100/123']), (100, 123))
        # and that it is hard to confuse
        self.assertEqual(parse_series_marker(['v2PATCH1/4']), (1, 4))
        self.assertEqual(parse_series_marker(['v2', 'PATCH1/4']), (1, 4))
        self.assertEqual(parse_series_marker(['v2.3PATCH1/4']), (1, 4))

    def test_version(self):
        self.assertEqual(parse_version('', []), 1)
        self.assertEqual(parse_version('Hello, world', []), 1)
        self.assertEqual(parse_version('Hello, world', ['version']), 1)
        self.assertEqual(parse_version('Hello, world', ['v2']), 2)
        self.assertEqual(parse_version('Hello, world', ['V6']), 6)
        self.assertEqual(parse_version('Hello, world', ['v10']), 10)
        self.assertEqual(parse_version('Hello, world (v2)', []), 2)
        self.assertEqual(parse_version('Hello, world (V6)', []), 6)


class FuzzTest(TransactionTestCase):
    """Test fuzzed patches."""
    def setUp(self):
        create_project(listid='patchwork.ozlabs.org')

    def _test_patch(self, name):
        file_path = os.path.join(TEST_FUZZ_DIR, name)
        m = load_mail(file_path)
        try:
            parse_mail(m, list_id='patchwork.ozlabs.org')
        except ValueError:
            pass

    @unittest.skipIf(six.PY2, 'Breaks only on Python 3')
    def test_early_fail(self):
        file_path = os.path.join(TEST_FUZZ_DIR, 'earlyfail.mbox')
        with self.assertRaises(AttributeError):
            load_mail(file_path)

    def test_base64err(self):
        self._test_patch('base64err.mbox')

    def test_codec(self):
        self._test_patch('codec-null.mbox')
        self._test_patch('charset.mbox')
        self._test_patch('unknown-encoding.mbox')
        self._test_patch('value2.mbox')

    def test_date(self):
        self._test_patch('date.mbox')
        self._test_patch('date-too-long.mbox')
        self._test_patch('year-out-of-range.mbox')
        self._test_patch('date-oserror.mbox')

    def test_length_for_db(self):
        self._test_patch('msgid-len.mbox')
        self._test_patch('msgid-len2.mbox')
        self._test_patch('email-len.mbox')
        self._test_patch('name-len.mbox')

    def test_hdr(self):
        self._test_patch('refshdr.mbox')
        self._test_patch('dateheader.mbox')
        self._test_patch('msgidheader.mbox')
