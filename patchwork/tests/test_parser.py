# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email
from email import message_from_string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
import os
import sys
import unittest

from django.test import TestCase
from django.test import TransactionTestCase
from django.db.transaction import atomic
from django.db import connection

from patchwork.models import Cover
from patchwork.models import CoverComment
from patchwork.models import Patch
from patchwork.models import PatchComment
from patchwork.models import Person
from patchwork.models import State
from patchwork import parser
from patchwork.parser import clean_subject
from patchwork.parser import get_or_create_author
from patchwork.parser import find_patch_content as find_content
from patchwork.parser import find_comment_content
from patchwork.parser import find_project
from patchwork.parser import find_series
from patchwork.parser import parse_mail as _parse_mail
from patchwork.parser import parse_pull_request
from patchwork.parser import parse_series_marker
from patchwork.parser import parse_version
from patchwork.parser import split_prefixes
from patchwork.parser import subject_check
from patchwork.parser import DuplicateMailError
from patchwork.tests import TEST_MAIL_DIR
from patchwork.tests import TEST_FUZZ_DIR
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_series_reference
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user
from patchwork.tests.utils import read_patch
from patchwork.tests.utils import SAMPLE_DIFF


def load_mail(file_path):
    with open(file_path, 'rb') as f:
        mail = email.message_from_binary_file(f)
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


def _create_email(
    msg,
    msgid=None,
    subject=None,
    sender=None,
    listid=None,
    in_reply_to=None,
    headers=None,
):
    msg['Message-Id'] = msgid or make_msgid()
    msg['Subject'] = subject or 'Test subject'
    msg['From'] = sender or 'Test Author <test-author@example.com>'
    msg['List-Id'] = listid or 'test.example.com'

    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to

    for header in headers or {}:
        msg[header] = headers[header]

    return msg


def create_email(
    content,
    msgid=None,
    subject=None,
    sender=None,
    listid=None,
    in_reply_to=None,
    headers=None,
):
    msg = MIMEText(content, _charset='us-ascii')

    return _create_email(
        msg, msgid, subject, sender, listid, in_reply_to, headers)


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
        person = get_or_create_author(email)
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
            get_or_create_author(email)

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
    """Validate correct behavior of the get_or_create_author case.

    Relies of checking the internal state of a Django model object.

    http://stackoverflow.com/a/19379636/613428
    """

    @staticmethod
    def _create_email(from_header, reply_tos=None, ccs=None,
                      x_original_from=None):
        mail = 'Message-Id: %s\n' % make_msgid() + \
               'From: %s\n' % from_header

        if reply_tos:
            mail += 'Reply-To: %s\n' % ', '.join(reply_tos)

        if ccs:
            mail += 'Cc: %s\n' % ', '.join(ccs)

        if x_original_from:
            mail += 'X-Original-From: %s\n' % x_original_from

        mail += 'Subject: Tests\n\n'\
            'test\n'

        return message_from_string(mail)

    def test_existing_sender(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        # create the person first
        person_a = get_or_create_author(mail)
        person_a.save()

        # then attempt to parse email with the same 'From' line
        person_b = get_or_create_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_existing_different_format(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        # create the person first
        person_a = get_or_create_author(mail)
        person_a.save()

        # then attempt to parse email with a new 'From' line
        mail = self._create_email('existing@example.com')
        person_b = get_or_create_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_existing_different_case(self):
        sender = 'Existing Sender <existing@example.com>'
        mail = self._create_email(sender)

        person_a = get_or_create_author(mail)
        person_a.save()

        mail = self._create_email(sender.upper())
        person_b = get_or_create_author(mail)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_mailman_dmarc_munging(self):
        project = create_project()
        real_sender = 'Existing Sender <existing@example.com>'
        munged_sender = 'Existing Sender via List <{}>'.format(
            project.listemail)
        other_email = 'Other Person <other@example.com>'

        # Unmunged author
        mail = self._create_email(real_sender)
        person_a = get_or_create_author(mail, project)
        person_a.save()

        # Single Reply-To
        mail = self._create_email(munged_sender, [real_sender])
        person_b = get_or_create_author(mail, project)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

        # Single Cc
        mail = self._create_email(munged_sender, [], [real_sender])
        person_b = get_or_create_author(mail, project)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

        # Multiple Reply-Tos and Ccs
        mail = self._create_email(munged_sender, [other_email, real_sender],
                                  [other_email, other_email])
        person_b = get_or_create_author(mail, project)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_google_dmarc_munging(self):
        project = create_project()
        real_sender = 'Existing Sender <existing@example.com>'
        munged_sender = "'Existing Sender' via List <{}>".format(
            project.listemail)

        # Unmunged author
        mail = self._create_email(real_sender)
        person_a = get_or_create_author(mail, project)
        person_a.save()

        # X-Original-From header
        mail = self._create_email(munged_sender, None, None, real_sender)
        person_b = get_or_create_author(mail, project)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

    def test_weird_dmarc_munging(self):
        project = create_project()
        real_sender = 'Existing Sender <existing@example.com>'
        munged_sender1 = "'Existing Sender' via <{}>".format(project.listemail)
        munged_sender2 = "'Existing Sender' <{}>".format(project.listemail)

        # Unmunged author
        mail = self._create_email(real_sender)
        person_a = get_or_create_author(mail, project)
        person_a.save()

        # Munged with no list name
        mail = self._create_email(munged_sender1, None, None, real_sender)
        person_b = get_or_create_author(mail, project)
        self.assertEqual(person_b._state.adding, False)
        self.assertEqual(person_b.id, person_a.id)

        # Munged with no 'via'
        mail = self._create_email(munged_sender2, None, None, real_sender)
        person_b = get_or_create_author(mail, project)
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

        self.assertFalse(find_series(project, email,
                                     get_or_create_author(email)))

    def test_first_reply(self):
        msgid_a = make_msgid()
        msgid_b = make_msgid()
        email = self._create_email(msgid_b, [msgid_a])

        # assume msgid_a was already handled
        ref = create_series_reference(msgid=msgid_a)

        series = find_series(ref.series.project, email,
                             get_or_create_author(email))
        self.assertEqual(series.first(), ref.series)

    def test_nested_series(self):
        """Handle a series sent in-reply-to an existing series."""
        # create an old series with a "cover letter"
        msgids = [make_msgid()]
        project = create_project()
        series_v1 = create_series(project=project)
        create_series_reference(msgid=msgids[0], series=series_v1,
                                project=project)

        # ...and three patches
        for i in range(3):
            msgids.append(make_msgid())
            create_series_reference(msgid=msgids[-1], series=series_v1,
                                    project=project)

        # now create a new series with "cover letter"
        msgids.append(make_msgid())
        series_v2 = create_series(project=project)
        ref_v2 = create_series_reference(msgid=msgids[-1], series=series_v2,
                                         project=project)

        # ...and the "first patch" of this new series
        msgid = make_msgid()
        email = self._create_email(msgid, msgids)
        series = find_series(project, email, get_or_create_author(email))

        # this should link to the second series - not the first
        self.assertEqual(len(msgids), 4 + 1)  # old series + new cover
        self.assertEqual(series.first(), ref_v2.series)


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
                PatchComment.objects.filter(patch=patch).count(), 1)


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

    def test_git_pull_newline_in_url(self):
        diff, message = self._find_content(
            '0023-git-pull-request-newline-in-url.mbox')
        pull_url = parse_pull_request(message)
        self.assertEqual(
            'https://git.kernel.org/pub/scm/linux/kernel/git/matthias.bgg/'
            'linux.git/ tags/v5.4-next-soc',
            pull_url)

    def test_git_pull_trailing_space(self):
        diff, message = self._find_content(
            '0024-git-pull-request-trailing-space.mbox')
        pull_url = parse_pull_request(message)
        self.assertEqual(
            'git://git.kernel.org/pub/scm/linux/kernel/git/nsekhar/'
            'linux-davinci.git tags/davinci-for-v5.6/soc',
            pull_url)

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

    def test_git_new_empty_file(self):
        diff, message = self._find_content('0021-git-empty-new-file.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)

    def test_git_mode_change(self):
        diff, message = self._find_content('0022-git-mode-change.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)

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

    def test_html_multipart(self):
        """Validate parsing a mail with multiple parts."""
        diff, message = self._find_content('0019-multipart-patch.mbox')
        self.assertTrue(diff is not None)
        self.assertTrue(message is not None)
        self.assertFalse('<div' in diff)
        self.assertFalse('<div' in message)


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


class CommentParseTest(TestCase):
    """Test parsing of different comment formats."""

    @staticmethod
    def _find_content(mbox_filename):
        mail = read_mail(mbox_filename)
        _, message = find_comment_content(mail)

        return message

    def test_html_multipart(self):
        """Validate parsing a mail with multiple parts."""
        message = self._find_content('0020-multipart-comment.mbox')
        self.assertTrue(message is not None)
        self.assertFalse('<div' in message)


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


class CommentActionRequiredTest(TestCase):

    fixtures = ['default_tags']

    def setUp(self):
        self.project = create_project(listid='test.example.com')

    def _create_submission_and_comments(self, submission_email):
        comment_a_email = create_email(
            'test comment\n',
            in_reply_to=submission_email['Message-Id'],
            listid=self.project.listid,
            headers={},
        )
        comment_b_email = create_email(
            'another test comment\n',
            in_reply_to=submission_email['Message-Id'],
            listid=self.project.listid,
            headers={'X-Patchwork-Action-Required': ''},
        )
        parse_mail(submission_email)
        parse_mail(comment_a_email)
        parse_mail(comment_b_email)

        comment_a_msgid = comment_a_email.get('Message-ID')
        comment_b_msgid = comment_b_email.get('Message-ID')

        return comment_a_msgid, comment_b_msgid

    def test_patch_comment(self):
        body = read_patch('0001-add-line.patch')
        patch_email = create_email(body, listid=self.project.listid)
        comment_a_msgid, comment_b_msgid = \
            self._create_submission_and_comments(patch_email)

        self.assertEqual(1, Patch.objects.count())
        self.assertEqual(2, PatchComment.objects.count())
        comment_a = PatchComment.objects.get(msgid=comment_a_msgid)
        self.assertIsNone(comment_a.addressed)
        comment_b = PatchComment.objects.get(msgid=comment_b_msgid)
        self.assertFalse(comment_b.addressed)

    def test_cover_comment(self):
        cover_email = create_email(
            'test cover letter',
            subject='[0/2] A cover letter',
            listid=self.project.listid)
        comment_a_msgid, comment_b_msgid = \
            self._create_submission_and_comments(cover_email)

        self.assertEqual(1, Cover.objects.count())
        self.assertEqual(2, CoverComment.objects.count())
        comment_a = CoverComment.objects.get(msgid=comment_a_msgid)
        self.assertIsNone(comment_a.addressed)
        comment_b = CoverComment.objects.get(msgid=comment_b_msgid)
        self.assertFalse(comment_b.addressed)


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
        self.assertEqual(clean_subject("[PATCH] meep,\n meep"),
                         ('meep, meep', []))
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


class SubjectMatchTest(TestCase):

    def setUp(self):
        self.list_id = 'test-subject-match.test.org'
        self.project_x = create_project(name='PROJECT X',
                                        listid=self.list_id,
                                        subject_match=r'.*PROJECT[\s]?X.*')
        self.default_project = create_project(name='Default',
                                              listid=self.list_id,
                                              subject_match=r'')
        self.keyword_project = create_project(name='keyword',
                                              listid=self.list_id,
                                              subject_match=r'keyword')

        self.email = MIMEText('')
        self.email['List-Id'] = self.list_id

        self.email_no_project = MIMEText('')
        self.email_no_project['List-Id'] = 'nonexistent-project.test.org'
        self.email_no_project['Subject'] = '[PATCH keyword]'

    def test_project_with_regex(self):
        self.email['Subject'] = '[PATCH PROJECT X subsystem]'
        project = find_project(self.email)
        self.assertEqual(project, self.project_x)

        self.email['Subject'] = '[PATCH PROJECTX another subsystem]'
        project = find_project(self.email)
        self.assertEqual(project, self.project_x)

    def test_project_with_keyword(self):
        self.email['Subject'] = '[PATCH keyword] subsystem'
        project = find_project(self.email)
        self.assertEqual(project, self.keyword_project)

    def test_default_project(self):
        self.email['Subject'] = '[PATCH unknown project]'
        project = find_project(self.email)
        self.assertEqual(project, self.default_project)

        self.email['Subject'] = '[PATCH NOT-PROJECT-X]'
        project = find_project(self.email)
        self.assertEqual(project, self.default_project)

    def test_nonexistent_project(self):
        project = find_project(self.email_no_project)
        self.assertEqual(project, None)

    def test_list_id_override(self):
        project = find_project(self.email_no_project,
                               self.keyword_project.listid)
        self.assertEqual(project, self.keyword_project)


class WeirdMailTest(TransactionTestCase):
    """Test fuzzed or otherwise weird patches."""

    def setUp(self):
        create_project(listid='patchwork.ozlabs.org')

    def _test_patch(self, name):
        file_path = os.path.join(TEST_FUZZ_DIR, name)
        m = load_mail(file_path)
        try:
            parse_mail(m, list_id='patchwork.ozlabs.org')
        except ValueError:
            pass

    @unittest.skipUnless((3, 0) <= sys.version_info < (3, 7),
                         'Breaks only on Python 3.0 - 3.6')
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

    def test_x_face(self):
        self._test_patch('x-face.mbox')


class DuplicateMailTest(TestCase):
    def setUp(self):
        self.listid = 'patchwork.ozlabs.org'
        create_project(listid=self.listid)
        create_state()

    def _test_duplicate_mail(self, mail):
        errors = []

        def log_query_errors(execute, sql, params, many, context):
            try:
                result = execute(sql, params, many, context)
            except Exception as e:
                errors.append(e)
                raise
            return result

        _parse_mail(mail)

        with self.assertRaises(DuplicateMailError):
            with connection.execute_wrapper(log_query_errors):
                # If we see any database errors from the duplicate insert
                # (typically an IntegrityError), the insert will abort the
                # current transaction. This atomic() ensures that we can
                # recover, and perform subsequent queries.
                with atomic():
                    _parse_mail(mail)

        self.assertEqual(errors, [])

    def test_duplicate_patch(self):
        diff = read_patch('0001-add-line.patch')
        m = create_email(diff, listid=self.listid, msgid='1@example.com')

        self._test_duplicate_mail(m)

        self.assertEqual(Patch.objects.count(), 1)

    def test_duplicate_comment(self):
        diff = read_patch('0001-add-line.patch')
        m1 = create_email(diff, listid=self.listid, msgid='1@example.com')
        _parse_mail(m1)

        m2 = create_email('test', listid=self.listid, msgid='2@example.com',
                          in_reply_to='1@example.com')
        self._test_duplicate_mail(m2)

        self.assertEqual(Patch.objects.count(), 1)
        self.assertEqual(PatchComment.objects.count(), 1)

    def test_duplicate_coverletter(self):
        m = create_email('test', listid=self.listid, msgid='1@example.com')
        del m['Subject']
        m['Subject'] = '[PATCH 0/1] test cover letter'

        self._test_duplicate_mail(m)

        self.assertEqual(Cover.objects.count(), 1)


class TestCommentCorrelation(TestCase):

    def test_find_patch_for_comment__no_reply(self):
        """Test behavior for mails that don't match anything we have."""
        project = create_project()
        create_patch(project=project)

        result = parser.find_patch_for_comment(project, ['foo'])

        self.assertIsNone(result)

    def test_find_patch_for_comment__direct_reply(self):
        """Test behavior when we have a reference to the original patch."""
        msgid = make_msgid()
        project = create_project()
        patch = create_patch(msgid=msgid, project=project)

        result = parser.find_patch_for_comment(project, [msgid])

        self.assertEqual(patch, result)

    def test_find_patch_for_comment__indirect_reply(self):
        """Test behavior when we only have a reference to a comment."""
        msgid = make_msgid()
        project = create_project()
        patch = create_patch(project=project)
        create_patch_comment(patch=patch, msgid=msgid)

        result = parser.find_patch_for_comment(project, [msgid])

        self.assertEqual(patch, result)

    def test_find_cover_for_comment__no_reply(self):
        """Test behavior for mails that don't match anything we have."""
        project = create_project()
        create_cover(project=project)

        result = parser.find_cover_for_comment(project, ['foo'])

        self.assertIsNone(result)

    def test_find_cover_for_comment__direct_reply(self):
        """Test behavior when we have a reference to the original cover."""
        msgid = make_msgid()
        project = create_project()
        cover = create_cover(msgid=msgid, project=project)

        result = parser.find_cover_for_comment(project, [msgid])

        self.assertEqual(cover, result)

    def test_find_cover_for_comment__indirect_reply(self):
        """Test behavior when we only have a reference to a comment."""
        msgid = make_msgid()
        project = create_project()
        cover = create_cover(project=project)
        create_cover_comment(cover=cover, msgid=msgid)

        result = parser.find_cover_for_comment(project, [msgid])

        self.assertEqual(cover, result)
