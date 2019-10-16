# vim: set fileencoding=utf-8 :

# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import dateutil.parser
import dateutil.tz
import email

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user


class MboxPatchResponseTest(TestCase):

    """Test that the mbox view appends the Acked-by from a patch comment."""

    def setUp(self):
        self.project = create_project()
        self.person = create_person()

    def test_patch_response(self):
        patch = create_patch(
            project=self.project,
            submitter=self.person,
            content='comment 1 text\nAcked-by: 1\n')
        create_comment(
            submission=patch,
            submitter=self.person,
            content='comment 2 text\nAcked-by: 2\n')
        response = self.client.get(
            reverse('patch-mbox', args=[self.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, 'Acked-by: 1\nAcked-by: 2\n')

    def test_patch_utf8_nbsp(self):
        patch = create_patch(
            project=self.project,
            submitter=self.person,
            content='patch text\n')
        create_comment(
            submission=patch,
            submitter=self.person,
            content=u'comment\nAcked-by:\u00A0 foo')
        response = self.client.get(
            reverse('patch-mbox', args=[self.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, u'\u00A0 foo\n')


class MboxPatchSplitResponseTest(TestCase):

    """Test that the mbox view appends the Acked-by from a patch comment,
       and places it before an '---' update line."""

    def setUp(self):
        self.project = create_project()
        self.person = create_person()
        self.patch = create_patch(
            project=self.project,
            submitter=self.person,
            diff='',
            content='comment 1 text\nAcked-by: 1\n---\nupdate\n')
        self.comment = create_comment(
            submission=self.patch,
            submitter=self.person,
            content='comment 2 text\nAcked-by: 2\n')

    def test_patch_response(self):
        response = self.client.get(
            reverse('patch-mbox', args=[self.project.linkname,
                                        self.patch.url_msgid]))
        self.assertContains(response, 'Acked-by: 1\nAcked-by: 2\n')


class MboxHeaderTest(TestCase):

    """Test the passthrough and generation of various headers."""

    def _test_header_passthrough(self, header):
        patch = create_patch(headers=header + '\n')
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, header)

    def test_header_passthrough_cc(self):
        """Validate passthrough of 'Cc' header."""
        header = 'Cc: CC Person <cc@example.com>'
        self._test_header_passthrough(header)

    def test_header_passthrough_to(self):
        """Validate passthrough of 'To' header."""
        header = 'To: To Person <to@example.com>'
        self._test_header_passthrough(header)

    def test_header_passthrough_date(self):
        """Validate passthrough of 'Date' header."""
        header = 'Date: Fri, 7 Jun 2013 15:42:54 +1000'
        self._test_header_passthrough(header)

    def test_header_passthrough_from(self):
        """Validate passthrough of 'From' header."""
        header = 'From: John Doe <john@doe.com>'
        self._test_header_passthrough(header)

    def test_header_passthrough_listid(self):
        """Validate passthrough of 'List-ID' header."""
        header = 'List-Id: Patchwork development <patchwork.lists.ozlabs.org>'
        self._test_header_passthrough(header)

    def _test_header_dropped(self, header):
        patch = create_patch(headers=header + '\n')
        response = self.client.get(reverse('patch-mbox',
                                           args=[patch.project.linkname,
                                                 patch.url_msgid]))
        self.assertNotContains(response, header)

    def test_header_dropped_content_transfer_encoding(self):
        """Validate dropping of 'Content-Transfer-Encoding' header."""
        header = 'Content-Transfer-Encoding: quoted-printable'
        self._test_header_dropped(header)

    def test_header_dropped_content_type_multipart_signed(self):
        """Validate dropping of 'Content-Type=multipart/signed' header."""
        header = 'Content-Type: multipart/signed'
        self._test_header_dropped(header)

    def test_patchwork_id_header(self):
        """Validate inclusion of generated 'X-Patchwork-Id' header."""
        patch = create_patch()
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, 'X-Patchwork-Id: %d' % patch.id)

    def test_patchwork_delegate_header(self):
        """Validate inclusion of generated 'X-Patchwork-Delegate' header."""
        user = create_user()
        patch = create_patch(delegate=user)
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, 'X-Patchwork-Delegate: %s' % user.email)

    def test_patchwork_from_header(self):
        """Validate inclusion of generated 'X-Patchwork-From' header."""
        email = 'jon@doe.com'
        from_header = 'From: Jon Doe <%s>\n' % email

        person = create_person(name='Jonathon Doe', email=email)
        patch = create_patch(submitter=person, headers=from_header)
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, from_header)
        self.assertContains(response, 'X-Patchwork-Submitter: %s <%s>' % (
            person.name, email))

    def test_from_header(self):
        """Validate non-ascii 'From' header.

        Test that a person with characters outside ASCII in his name do
        produce correct From header. As RFC 2822 state we must retain
        the <user@domain.tld> format for the mail while the name part
        may be coded in some ways.
        """
        person = create_person(name=u'©ool guŷ')
        patch = create_patch(submitter=person)
        from_email = '<' + person.email + '>'
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        self.assertContains(response, from_email)

    def test_dmarc_from_header(self):
        """Validate 'From' header is rewritten correctly when DMARC-munged.

        Test that when an email with a DMARC-munged From header is processed,
        the From header will be unmunged and the munged address will be saved
        as 'X-Patchwork-Original-From'.
        """
        orig_from_header = 'Person via List <list@example.com>'
        rewritten_from_header = 'Person <person@example.com>'
        project = create_project(listemail='list@example.com')
        person = create_person(name='Person', email='person@example.com')
        patch = create_patch(project=project,
                             headers='From: ' + orig_from_header,
                             submitter=person)
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        mail = email.message_from_string(response.content.decode())
        self.assertEqual(mail['From'], rewritten_from_header)
        self.assertEqual(mail['X-Patchwork-Original-From'], orig_from_header)

    def test_date_header(self):
        patch = create_patch()
        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        mail = email.message_from_string(response.content.decode())
        mail_date = dateutil.parser.parse(mail['Date'])
        # patch dates are all in UTC
        patch_date = patch.date.replace(tzinfo=dateutil.tz.tzutc(),
                                        microsecond=0)
        self.assertEqual(mail_date, patch_date)

    def test_supplied_date_header(self):
        patch = create_patch()
        offset = 3 * 60 * 60  # 3 (hours) * 60 (minutes) * 60 (seconds)
        tz = dateutil.tz.tzoffset(None, offset)
        date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        date = date.replace(tzinfo=tz, microsecond=0)

        patch.headers = 'Date: %s\n' % date.strftime("%a, %d %b %Y %T %z")
        patch.save()

        response = self.client.get(
            reverse('patch-mbox', args=[patch.project.linkname,
                                        patch.url_msgid]))
        mail = email.message_from_string(response.content.decode())
        mail_date = dateutil.parser.parse(mail['Date'])
        self.assertEqual(mail_date, date)


class MboxCommentPostcriptUnchangedTest(TestCase):

    def test_comment_unchanged(self):
        """Validate postscript part of mail is unchanged.

        Test that the mbox view doesn't change the postscript part of
        a mail. There where always a missing blank right after the
        postscript delimiter '---' and an additional newline right
        before.
        """
        content = 'some comment\n---\n some/file | 1 +\n'
        project = create_project()
        patch = create_patch(content=content, diff='', project=project)

        response = self.client.get(
            reverse('patch-mbox', args=[project.linkname, patch.url_msgid]))

        self.assertContains(response, content)
        self.assertNotContains(response, content + '\n')


class MboxSeriesDependencies(TestCase):

    @staticmethod
    def _create_patches():
        series = create_series()
        patch_a = create_patch(series=series)
        patch_b = create_patch(series=series)

        return series, patch_a, patch_b

    def test_patch_with_wildcard_series(self):
        _, patch_a, patch_b = self._create_patches()

        response = self.client.get('%s?series=*' % reverse(
            'patch-mbox', args=[patch_b.patch.project.linkname,
                                patch_b.patch.url_msgid]))

        self.assertContains(response, patch_a.content)
        self.assertContains(response, patch_b.content)

    def test_patch_with_numeric_series(self):
        series, patch_a, patch_b = self._create_patches()

        response = self.client.get('%s?series=%d' % (
            reverse('patch-mbox', args=[patch_b.patch.project.linkname,
                                        patch_b.patch.url_msgid]),
            series.id))

        self.assertContains(response, patch_a.content)
        self.assertContains(response, patch_b.content)

    def test_patch_with_invalid_series(self):
        series, patch_a, patch_b = self._create_patches()

        for value in ('foo', str(series.id + 1)):
            response = self.client.get('%s?series=%s' % (
                reverse('patch-mbox', args=[patch_b.patch.project.linkname,
                                            patch_b.patch.url_msgid]), value))

            self.assertEqual(response.status_code, 404)

    def test_legacy_patch(self):
        """Validate a patch with non-existent dependencies raises a 404."""
        # we're explicitly creating a patch without a series
        patch = create_patch(series=None)

        response = self.client.get('%s?series=*' % reverse(
            'patch-mbox', args=[patch.project.linkname, patch.url_msgid]))

        self.assertEqual(response.status_code, 404)


class MboxSeries(TestCase):

    def test_series(self):
        series = create_series()
        patch_a = create_patch(series=series)
        patch_b = create_patch(series=series)

        response = self.client.get(reverse('series-mbox', args=[series.id]))

        self.assertContains(response, patch_a.content)
        self.assertContains(response, patch_b.content)
