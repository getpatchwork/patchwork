# Patchwork - automated patch tracking system
# Copyright (C) 2014 Jeremy Kerr <jk@ozlabs.org>
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
import datetime
from django.test import TestCase, TransactionTestCase
from patchwork.models import Project, Patch, Comment, Tag, PatchTag
from patchwork.tests.utils import defaults
from patchwork.parser import extract_tags

from django.conf import settings
from django.db import connection

class ExtractTagsTest(TestCase):

    email = 'test@exmaple.com'
    name_email = 'test name <' + email + '>'
    fixtures = ['default_tags', 'default_states']

    def assertTagsEqual(self, str, acks, reviews, tests):
        counts = extract_tags(str, Tag.objects.all())
        self.assertEquals((acks, reviews, tests),
                (counts[Tag.objects.get(name='Acked-by')],
                 counts[Tag.objects.get(name='Reviewed-by')],
                 counts[Tag.objects.get(name='Tested-by')]))

    def testEmpty(self):
        self.assertTagsEqual("", 0, 0, 0)

    def testNoTag(self):
        self.assertTagsEqual("foo", 0, 0, 0)

    def testAck(self):
        self.assertTagsEqual("Acked-by: %s" % self.name_email, 1, 0, 0)

    def testAckEmailOnly(self):
        self.assertTagsEqual("Acked-by: %s" % self.email, 1, 0, 0)

    def testReviewed(self):
        self.assertTagsEqual("Reviewed-by: %s" % self.name_email, 0, 1, 0)

    def testTested(self):
        self.assertTagsEqual("Tested-by: %s" % self.name_email, 0, 0, 1)

    def testAckAfterNewline(self):
        self.assertTagsEqual("\nAcked-by: %s" % self.name_email, 1, 0, 0)

    def testMultipleAcks(self):
        str = "Acked-by: %s\nAcked-by: %s\n" % ((self.name_email,) * 2)
        self.assertTagsEqual(str, 2, 0, 0)

    def testMultipleTypes(self):
        str = "Acked-by: %s\nAcked-by: %s\nReviewed-by: %s\n" % (
                (self.name_email,) * 3)
        self.assertTagsEqual(str, 2, 1, 0)

    def testLower(self):
        self.assertTagsEqual("acked-by: %s" % self.name_email, 1, 0, 0)

    def testUpper(self):
        self.assertTagsEqual("ACKED-BY: %s" % self.name_email, 1, 0, 0)

    def testAckInReply(self):
        self.assertTagsEqual("> Acked-by: %s\n" % self.name_email, 0, 0, 0)

class PatchTagsTest(TransactionTestCase):
    ACK = 1
    REVIEW = 2
    TEST = 3
    fixtures = ['default_tags', 'default_states']

    def assertTagsEqual(self, patch, acks, reviews, tests):
        patch = Patch.objects.get(pk=patch.pk)

        def count(name):
            try:
                return patch.patchtag_set.get(tag__name=name).count
            except PatchTag.DoesNotExist:
                return 0

        counts = (
            count(name='Acked-by'),
            count(name='Reviewed-by'),
            count(name='Tested-by'),
        )

        self.assertEqual(counts, (acks, reviews, tests))

    def create_tag(self, tagtype = None):
        tags = {
            self.ACK: 'Acked',
            self.REVIEW: 'Reviewed',
            self.TEST: 'Tested'
        }
        if tagtype not in tags:
            return ''
        return '%s-by: %s\n' % (tags[tagtype], self.tagger)

    def create_tag_comment(self, patch, tagtype = None):
        comment = Comment(patch=patch, msgid=str(datetime.datetime.now()),
                submitter=defaults.patch_author_person,
                content=self.create_tag(tagtype))
        comment.save()
        return comment

    def setUp(self):
        settings.DEBUG = True
        project = Project(linkname='test-project', name='Test Project',
            use_tags=True)
        project.save()
        defaults.patch_author_person.save()
        self.patch = Patch(project=project,
                           msgid='x', name=defaults.patch_name,
                           submitter=defaults.patch_author_person,
                           content='')
        self.patch.save()
        self.tagger = 'Test Tagger <tagger@example.com>'

    def tearDown(self):
        self.patch.delete()

    def testNoComments(self):
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def testNoTagComment(self):
        self.create_tag_comment(self.patch, None)
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def testSingleComment(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)

    def testMultipleComments(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def testMultipleCommentTypes(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.create_tag_comment(self.patch, self.REVIEW)
        self.create_tag_comment(self.patch, self.TEST)
        self.assertTagsEqual(self.patch, 1, 1, 1)

    def testCommentAdd(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def testCommentUpdate(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)

        comment.content += self.create_tag(self.ACK)
        comment.save()
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def testCommentDelete(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)
        comment.delete()
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def testSingleCommentMultipleTags(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        comment.content += self.create_tag(self.REVIEW)
        comment.save()
        self.assertTagsEqual(self.patch, 1, 1, 0)

    def testMultipleCommentsMultipleTags(self):
        c1 = self.create_tag_comment(self.patch, self.ACK)
        c1.content += self.create_tag(self.REVIEW)
        c1.save()
        self.assertTagsEqual(self.patch, 1, 1, 0)

class PatchTagManagerTest(PatchTagsTest):

    def assertTagsEqual(self, patch, acks, reviews, tests):

        tagattrs = {}
        for tag in Tag.objects.all():
            tagattrs[tag.name] = tag.attr_name

        # force project.tags to be queried outside of the assertNumQueries
        patch.project.tags

        # we should be able to do this with two queries: one for
        # the patch table lookup, and the prefetch_related for the
        # projects table.
        with self.assertNumQueries(2):
            patch = Patch.objects.with_tag_counts(project=patch.project) \
                    .get(pk = patch.pk)

            counts = (
                getattr(patch, tagattrs['Acked-by']),
                getattr(patch, tagattrs['Reviewed-by']),
                getattr(patch, tagattrs['Tested-by']),
            )

        self.assertEqual(counts, (acks, reviews, tests))

