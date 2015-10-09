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

import unittest
import email
import datetime
import dateutil.parser, dateutil.tz
from django.test import TestCase
from django.test.client import Client
from patchwork.models import Patch, Comment, Person
from patchwork.tests.utils import defaults, create_user, find_in_context

class MboxPatchResponseTest(TestCase):
    fixtures = ['default_states']

    """ Test that the mbox view appends the Acked-by from a patch comment """
    def setUp(self):
        defaults.project.save()

        self.person = defaults.patch_author_person
        self.person.save()

        self.patch = Patch(project = defaults.project,
                           msgid = 'p1', name = 'testpatch',
                           submitter = self.person, content = '')
        self.patch.save()
        comment = Comment(patch = self.patch, msgid = 'p1',
                submitter = self.person,
                content = 'comment 1 text\nAcked-by: 1\n')
        comment.save()

        comment = Comment(patch = self.patch, msgid = 'p2',
                submitter = self.person,
                content = 'comment 2 text\nAcked-by: 2\n')
        comment.save()

    def testPatchResponse(self):
        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response,
                'Acked-by: 1\nAcked-by: 2\n')

class MboxPatchSplitResponseTest(TestCase):
    fixtures = ['default_states']

    """ Test that the mbox view appends the Acked-by from a patch comment,
        and places it before an '---' update line. """
    def setUp(self):
        defaults.project.save()

        self.person = defaults.patch_author_person
        self.person.save()

        self.patch = Patch(project = defaults.project,
                           msgid = 'p1', name = 'testpatch',
                           submitter = self.person, content = '')
        self.patch.save()
        comment = Comment(patch = self.patch, msgid = 'p1',
                submitter = self.person,
                content = 'comment 1 text\nAcked-by: 1\n---\nupdate\n')
        comment.save()

        comment = Comment(patch = self.patch, msgid = 'p2',
                submitter = self.person,
                content = 'comment 2 text\nAcked-by: 2\n')
        comment.save()

    def testPatchResponse(self):
        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response,
                'Acked-by: 1\nAcked-by: 2\n')

class MboxPassThroughHeaderTest(TestCase):
    fixtures = ['default_states']

    """ Test that we see 'Cc' and 'To' headers passed through from original
        message to mbox view """

    def setUp(self):
        defaults.project.save()
        self.person = defaults.patch_author_person
        self.person.save()

        self.cc_header = 'Cc: CC Person <cc@example.com>'
        self.to_header = 'To: To Person <to@example.com>'
        self.date_header = 'Date: Fri, 7 Jun 2013 15:42:54 +1000'

        self.patch = Patch(project = defaults.project,
                           msgid = 'p1', name = 'testpatch',
                           submitter = self.person, content = '')

    def testCCHeader(self):
        self.patch.headers = self.cc_header + '\n'
        self.patch.save()

        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response, self.cc_header)

    def testToHeader(self):
        self.patch.headers = self.to_header + '\n'
        self.patch.save()

        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response, self.to_header)

    def testDateHeader(self):
        self.patch.headers = self.date_header + '\n'
        self.patch.save()

        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response, self.date_header)

class MboxBrokenFromHeaderTest(TestCase):
    fixtures = ['default_states']

    """ Test that a person with characters outside ASCII in his name do
        produce correct From header. As RFC 2822 state we must retain the
        <user@domain.tld> format for the mail while the name part may be coded
        in some ways. """

    def setUp(self):
        defaults.project.save()
        self.person = defaults.patch_author_person
        self.person.name = u'©ool guŷ'
        self.person.save()

        self.patch = Patch(project = defaults.project,
                msgid = 'p1', name = 'testpatch',
                submitter = self.person, content = '')

    def testFromHeader(self):
        self.patch.save()
        from_email = '<' + self.person.email + '>'

        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response, from_email)

class MboxDateHeaderTest(TestCase):
    fixtures = ['default_states']

    """ Test that the date provided in the patch mail view is correct """

    def setUp(self):
        defaults.project.save()
        self.person = defaults.patch_author_person
        self.person.save()

        self.patch = Patch(project = defaults.project,
                           msgid = 'p1', name = 'testpatch',
                           submitter = self.person, content = '')
        self.patch.save()

    def testDateHeader(self):
        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        mail = email.message_from_string(response.content)
        mail_date = dateutil.parser.parse(mail['Date'])
        # patch dates are all in UTC
        patch_date = self.patch.date.replace(tzinfo=dateutil.tz.tzutc(),
                                            microsecond=0)
        self.assertEqual(mail_date, patch_date)

    def testSuppliedDateHeader(self):
        hour_offset = 3
        tz = dateutil.tz.tzoffset(None, hour_offset * 60 * 60)
        date = datetime.datetime.utcnow() - datetime.timedelta(days = 1)
        date = date.replace(tzinfo=tz, microsecond=0)

        self.patch.headers = 'Date: %s\n' % date.strftime("%a, %d %b %Y %T %z")
        self.patch.save()

        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        mail = email.message_from_string(response.content)
        mail_date = dateutil.parser.parse(mail['Date'])
        self.assertEqual(mail_date, date)

class MboxCommentPostcriptUnchangedTest(TestCase):
    fixtures = ['default_states']

    """ Test that the mbox view doesn't change the postscript part of a mail.
        There where always a missing blank right after the postscript
        delimiter '---' and an additional newline right before. """
    def setUp(self):
        defaults.project.save()

        self.person = defaults.patch_author_person
        self.person.save()

        self.patch = Patch(project = defaults.project,
                           msgid = 'p1', name = 'testpatch',
                           submitter = self.person, content = '')
        self.patch.save()

        self.txt = 'some comment\n---\n some/file | 1 +\n'

        comment = Comment(patch = self.patch, msgid = 'p1',
                submitter = self.person,
                content = self.txt)
        comment.save()

    def testCommentUnchanged(self):
        response = self.client.get('/patch/%d/mbox/' % self.patch.id)
        self.assertContains(response, self.txt)
        self.txt += "\n"
        self.assertNotContains(response, self.txt)
