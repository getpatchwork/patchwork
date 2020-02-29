# Patchwork - automated patch tracking system
# Copyright (C) 2014 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.test import TransactionTestCase

from patchwork.models import Patch
from patchwork.models import PatchTag
from patchwork.models import Tag
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment


class ExtractTagsTest(TestCase):

    fixtures = ['default_tags']
    email = 'test@example.com'
    name_email = 'test name <' + email + '>'

    def assertTagsEqual(self, str, acks, reviews, tests):  # noqa
        counts = Patch.extract_tags(str, Tag.objects.all())
        self.assertEqual((acks, reviews, tests),
                         (counts[Tag.objects.get(name='Acked-by')],
                          counts[Tag.objects.get(name='Reviewed-by')],
                          counts[Tag.objects.get(name='Tested-by')]))

    def test_empty(self):
        self.assertTagsEqual('', 0, 0, 0)

    def test_no_tag(self):
        self.assertTagsEqual('foo', 0, 0, 0)

    def test_ack(self):
        self.assertTagsEqual('Acked-by: %s' % self.name_email, 1, 0, 0)

    def test_ack_email_only(self):
        self.assertTagsEqual('Acked-by: %s' % self.email, 1, 0, 0)

    def test_reviewed(self):
        self.assertTagsEqual('Reviewed-by: %s' % self.name_email, 0, 1, 0)

    def test_tested(self):
        self.assertTagsEqual('Tested-by: %s' % self.name_email, 0, 0, 1)

    def test_ack_after_newline(self):
        self.assertTagsEqual('\nAcked-by: %s' % self.name_email, 1, 0, 0)

    def test_multiple_acks(self):
        str = 'Acked-by: %s\nAcked-by: %s\n' % ((self.name_email,) * 2)
        self.assertTagsEqual(str, 2, 0, 0)

    def test_multiple_types(self):
        str = 'Acked-by: %s\nAcked-by: %s\nReviewed-by: %s\n' % (
            (self.name_email,) * 3)
        self.assertTagsEqual(str, 2, 1, 0)

    def test_lower(self):
        self.assertTagsEqual('acked-by: %s' % self.name_email, 1, 0, 0)

    def test_upper(self):
        self.assertTagsEqual('ACKED-BY: %s' % self.name_email, 1, 0, 0)

    def test_ack_in_reply(self):
        self.assertTagsEqual('> Acked-by: %s\n' % self.name_email, 0, 0, 0)


class PatchTagsTest(TransactionTestCase):

    fixtures = ['default_tags']
    ACK = 1
    REVIEW = 2
    TEST = 3

    def setUp(self):
        self.patch = create_patch()
        self.patch.project.use_tags = True
        self.patch.project.save()

    def assertTagsEqual(self, patch, acks, reviews, tests):  # noqa
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

    def create_tag(self, tagtype=None):
        tags = {
            self.ACK: 'Acked',
            self.REVIEW: 'Reviewed',
            self.TEST: 'Tested'
        }
        if tagtype not in tags:
            return ''

        return '%s-by: Test Tagger <tagger@example.com>\n' % tags[tagtype]

    def create_tag_comment(self, patch, tagtype=None):
        comment = create_patch_comment(
            patch=patch,
            content=self.create_tag(tagtype))
        return comment

    def test_no_comments(self):
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def test_no_tag_comment(self):
        self.create_tag_comment(self.patch, None)
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def test_single_comment(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)

    def test_multiple_comments(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def test_multiple_comment_types(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.create_tag_comment(self.patch, self.REVIEW)
        self.create_tag_comment(self.patch, self.TEST)
        self.assertTagsEqual(self.patch, 1, 1, 1)

    def test_comment_add(self):
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)
        self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def test_comment_update(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)

        comment.content += self.create_tag(self.ACK)
        comment.save()
        self.assertTagsEqual(self.patch, 2, 0, 0)

    def test_comment_delete(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        self.assertTagsEqual(self.patch, 1, 0, 0)
        comment.delete()
        self.assertTagsEqual(self.patch, 0, 0, 0)

    def test_single_comment_multiple_tags(self):
        comment = self.create_tag_comment(self.patch, self.ACK)
        comment.content += self.create_tag(self.REVIEW)
        comment.save()
        self.assertTagsEqual(self.patch, 1, 1, 0)

    def test_multiple_comments_multiple_tags(self):
        c1 = self.create_tag_comment(self.patch, self.ACK)
        c1.content += self.create_tag(self.REVIEW)
        c1.save()
        self.assertTagsEqual(self.patch, 1, 1, 0)


class PatchTagManagerTest(PatchTagsTest):

    def assertTagsEqual(self, patch, acks, reviews, tests):  # noqa
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
                .get(pk=patch.pk)

            counts = (
                getattr(patch, tagattrs['Acked-by']),
                getattr(patch, tagattrs['Reviewed-by']),
                getattr(patch, tagattrs['Tested-by']),
            )

        self.assertEqual(counts, (acks, reviews, tests))
