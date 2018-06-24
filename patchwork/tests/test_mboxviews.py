# vim: set fileencoding=utf-8 :
#
# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
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
from patchwork.tests.utils import create_series_patch
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
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
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
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
        self.assertContains(response, u'\u00A0 foo\n')


class MboxPatchSplitResponseTest(TestCase):

    """Test that the mbox view appends the Acked-by from a patch comment,
       and places it before an '---' update line."""

    def setUp(self):
        project = create_project()
        self.person = create_person()
        self.patch = create_patch(
            project=project,
            submitter=self.person,
            diff='',
            content='comment 1 text\nAcked-by: 1\n---\nupdate\n')
        self.comment = create_comment(
            submission=self.patch,
            submitter=self.person,
            content='comment 2 text\nAcked-by: 2\n')

    def test_patch_response(self):
        response = self.client.get(reverse('patch-mbox', args=[self.patch.id]))
        self.assertContains(response, 'Acked-by: 1\nAcked-by: 2\n')


class MboxHeaderTest(TestCase):

    """Test the passthrough and generation of various headers."""

    def _test_header_passthrough(self, header):
        patch = create_patch(headers=header + '\n')
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
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

    def test_patchwork_id_header(self):
        """Validate inclusion of generated 'X-Patchwork-Id' header."""
        patch = create_patch()
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
        self.assertContains(response, 'X-Patchwork-Id: %d' % patch.id)

    def test_patchwork_delegate_header(self):
        """Validate inclusion of generated 'X-Patchwork-Delegate' header."""
        user = create_user()
        patch = create_patch(delegate=user)
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
        self.assertContains(response, 'X-Patchwork-Delegate: %s' % user.email)

    def test_patchwork_from_header(self):
        """Validate inclusion of generated 'X-Patchwork-From' header."""
        email = 'jon@doe.com'
        from_header = 'From: Jon Doe <%s>\n' % email

        person = create_person(name='Jonathon Doe', email=email)
        patch = create_patch(submitter=person, headers=from_header)
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
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
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
        self.assertContains(response, from_email)

    def test_date_header(self):
        patch = create_patch()
        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
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

        response = self.client.get(reverse('patch-mbox', args=[patch.id]))
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
        patch = create_patch(content=content, diff='')

        response = self.client.get(reverse('patch-mbox', args=[patch.id]))

        self.assertContains(response, content)
        self.assertNotContains(response, content + '\n')


class MboxSeriesDependencies(TestCase):

    def test_patch_with_dependencies(self):
        patch_a = create_series_patch()
        patch_b = create_series_patch(series=patch_a.series)

        response = self.client.get('%s?series=*' % reverse(
            'patch-mbox', args=[patch_b.patch.id]))

        self.assertContains(response, patch_a.patch.content)
        self.assertContains(response, patch_b.patch.content)

    def test_legacy_patch(self):
        """Validate a patch with non-existent dependencies raises a 404."""
        # we're explicitly creating a patch without a series
        patch = create_patch()

        response = self.client.get('%s?series=*' % reverse(
            'patch-mbox', args=[patch.id]))

        self.assertEqual(response.status_code, 404)
