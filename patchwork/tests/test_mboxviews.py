# vim: set fileencoding=utf-8 :

# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import dateutil.parser
import dateutil.tz
import email

from django.http import Http404
from django.test import TestCase

from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_series
from patchwork.tests.utils import create_user
from patchwork.views import utils


class MboxPatchResponseTest(TestCase):

    def test_tags(self):
        """Test that tags are taken from a patch comment."""
        patch = create_patch(content='comment 1 text\nAcked-by: 1\n')
        create_patch_comment(
            patch=patch, content='comment 2 text\nAcked-by: 2\n')

        mbox = utils.patch_to_mbox(patch)
        self.assertIn('Acked-by: 1\nAcked-by: 2\n', mbox)

    def test_utf8_nbsp_tags(self):
        """Test that UTF-8 NBSP characters are correctly handled."""
        patch = create_patch(content='patch text\n')
        create_patch_comment(
            patch=patch, content=u'comment\nAcked-by:\u00A0 foo')

        mbox = utils.patch_to_mbox(patch)
        self.assertIn(u'\u00A0 foo\n', mbox)

    def test_multiple_tags(self):
        """Test that the mbox view appends tags correct.

        Ensure the tags are extracted from a patch comment, and placed before
        an '---' update line.
        """
        self.project = create_project()
        self.person = create_person()
        self.patch = create_patch(
            project=self.project,
            submitter=self.person,
            diff='',
            content='comment 1 text\nAcked-by: 1\n---\nupdate\n')
        self.comment = create_patch_comment(
            patch=self.patch,
            submitter=self.person,
            content='comment 2 text\nAcked-by: 2\n')

        mbox = utils.patch_to_mbox(self.patch)
        self.assertIn('Acked-by: 1\nAcked-by: 2\n', mbox)

    def _test_header_passthrough(self, header):
        patch = create_patch(headers=header + '\n')
        mbox = utils.patch_to_mbox(patch)
        self.assertIn(header, mbox)

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
        mbox = utils.patch_to_mbox(patch)
        self.assertNotIn(header, mbox)

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
        mbox = utils.patch_to_mbox(patch)
        self.assertIn('X-Patchwork-Id: %d' % patch.id, mbox)

    def test_patchwork_delegate_header(self):
        """Validate inclusion of generated 'X-Patchwork-Delegate' header."""
        user = create_user()
        patch = create_patch(delegate=user)
        mbox = utils.patch_to_mbox(patch)
        self.assertIn('X-Patchwork-Delegate: %s' % user.email, mbox)

    def test_patchwork_submitter_header(self):
        """Validate inclusion of generated 'X-Patchwork-Submitter' header."""
        email = 'jon@doe.com'
        from_header = f'From: Jon Doe <{email}>\n'
        person = create_person(name='Jonathon Doe', email=email)
        submitter_header = f'X-Patchwork-Submitter: {person.name} <{email}>'

        patch = create_patch(submitter=person, headers=from_header)

        mbox = utils.patch_to_mbox(patch)
        self.assertIn(from_header, mbox)
        self.assertIn(submitter_header, mbox)

    def test_from_header(self):
        """Validate non-ascii 'From' header.

        Test that a person with characters outside ASCII in his name do
        produce correct From header. As RFC 2822 state we must retain
        the <user@domain.tld> format for the mail while the name part
        may be coded in some ways.
        """
        person = create_person(name=u'©ool guŷ')
        patch = create_patch(submitter=person)
        from_email = f'<{person.email}>'
        mbox = utils.patch_to_mbox(patch)
        self.assertIn(from_email, mbox)

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
        mbox = utils.patch_to_mbox(patch)
        mail = email.message_from_string(mbox)
        self.assertEqual(mail['From'], rewritten_from_header)
        self.assertEqual(mail['X-Patchwork-Original-From'], orig_from_header)

    def test_date_header(self):
        patch = create_patch()
        mbox = utils.patch_to_mbox(patch)
        mail = email.message_from_string(mbox)
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

        mbox = utils.patch_to_mbox(patch)
        mail = email.message_from_string(mbox)
        mail_date = dateutil.parser.parse(mail['Date'])
        self.assertEqual(mail_date, date)

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

        mbox = utils.patch_to_mbox(patch)

        self.assertIn(content, mbox)
        self.assertNotIn(content + '\n', mbox)


class MboxSeriesPatchTest(TestCase):

    @staticmethod
    def _create_patches():
        series = create_series()
        patch_a = create_patch(series=series)
        patch_b = create_patch(series=series)

        return series, patch_a, patch_b

    def test_patch_with_wildcard_series(self):
        _, patch_a, patch_b = self._create_patches()

        mbox = utils.series_patch_to_mbox(patch_b, '*')

        self.assertIn(patch_a.content, mbox)
        self.assertIn(patch_b.content, mbox)

    def test_patch_with_numeric_series(self):
        series, patch_a, patch_b = self._create_patches()

        mbox = utils.series_patch_to_mbox(patch_b, series.id)

        self.assertIn(patch_a.content, mbox)
        self.assertIn(patch_b.content, mbox)

    def test_patch_with_invalid_series(self):
        series, patch_a, patch_b = self._create_patches()

        for value in ('foo', str(series.id + 1)):
            with self.assertRaises(Http404):
                utils.series_patch_to_mbox(patch_b, value)

    def test_legacy_patch(self):
        """Validate a patch with non-existent dependencies raises a 404."""
        # we're explicitly creating a patch without a series
        patch = create_patch(series=None)

        with self.assertRaises(Http404):
            utils.series_patch_to_mbox(patch, '*')


class MboxSeriesTest(TestCase):

    def test_series(self):
        series = create_series()
        patch_a = create_patch(series=series)
        patch_b = create_patch(series=series)

        mbox = utils.series_to_mbox(series)

        self.assertIn(patch_a.content, mbox)
        self.assertIn(patch_b.content, mbox)
