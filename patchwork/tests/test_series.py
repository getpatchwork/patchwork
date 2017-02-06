# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
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

import mailbox
import os

from django.test import TestCase

from patchwork import models
from patchwork import parser
from patchwork.tests import utils


TEST_SERIES_DIR = os.path.join(os.path.dirname(__file__), 'series')


class _BaseTestCase(TestCase):

    def setUp(self):
        utils.create_state()

    def _parse_mbox(self, name, counts, project=None):
        """Parse an mbox file and return the results.

        :param name: Name of mbox file
        :param counts: A three-tuple of expected number of cover
            letters, patches and replies parsed
        """
        results = [[], [], []]
        project = project or utils.create_project()

        mbox = mailbox.mbox(os.path.join(TEST_SERIES_DIR, name))
        for msg in mbox:
            obj = parser.parse_mail(msg, project.listid)
            if type(obj) == models.CoverLetter:
                results[0].append(obj)
            elif type(obj) == models.Patch:
                results[1].append(obj)
            else:
                results[2].append(obj)

        self.assertParsed(results, counts)

        return results

    def assertParsed(self, results, counts):
        self.assertEqual([len(x) for x in results], counts)

    def assertSerialized(self, patches, counts):
        """Validate correct series-ification.

        TODO(stephen): Eventually this should ensure the series
          revisions correctly linked and ordered in a series group

        :param patches: list of Patch instances
        :param count: list of integers corrsponding to number of
            patches per series
        """
        series = models.Series.objects.all().order_by('date')

        # sanity checks
        self.assertEqual(series.count(), len(counts))
        self.assertEqual(sum(counts), len(patches))

        # walk through each series, ensuring each indexed patch
        # corresponds to the correct series
        start_idx = 0
        for idx, count in enumerate(counts):
            end_idx = start_idx + count

            patches_ = patches[start_idx:end_idx]
            for patch in patches_:
                self.assertEqual(patch.latest_series, series[idx])

            start_idx = end_idx


class BaseSeriesTest(_BaseTestCase):
    """Tests for a series without any revisions."""

    def test_cover_letter(self):
        """Series with a cover letter.

        Parse a series with a cover letter and two patches.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, comments = self._parse_mbox(
            'base-cover-letter.mbox', [1, 2, 0])

        self.assertSerialized(patches, [2])
        self.assertSerialized(covers, [1])

    def test_no_cover_letter(self):
        """Series without a cover letter.

        Parse a series with two patches but no cover letter.

        Input:

          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        _, patches, _ = self._parse_mbox(
            'base-no-cover-letter.mbox', [0, 2, 0])

        self.assertSerialized(patches, [2])

    def test_out_of_order(self):
        """Series received out of order.

        Parse a series with a cover letter and two patches that is
        received out of order.

        Input:

            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH 1/2] test: Add some lorem ipsum
          - [PATCH 0/2] A sample series
        """
        covers, patches, comments = self._parse_mbox(
            'base-out-of-order.mbox', [1, 2, 0])

        self.assertSerialized(patches, [2])
        self.assertSerialized(covers, [1])

    def test_duplicated(self):
        """Series received on multiple mailing lists.

        Parse a series with a two patches sent to two mailing lists
        at the same time.

        Input:

          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        project_a = utils.create_project()
        project_b = utils.create_project()

        _, patches_a, _ = self._parse_mbox(
            'base-no-cover-letter.mbox', [0, 2, 0], project=project_a)
        _, patches_b, _ = self._parse_mbox(
            'base-no-cover-letter.mbox', [0, 2, 0], project=project_b)

        self.assertSerialized(patches_a + patches_b, [2, 2])


class RevisedSeriesTest(_BaseTestCase):
    """Tests for a series plus a single revision.

    NOTE(stephenfin): In each sample mbox, it is necessary to ensure
      the first series is placed before the revision. If not, they will
      not be parsed correctly. This is OK as in practice it would very
      unlikely to receive a revision before a previous revision.
    """

    def test_basic(self):
        """Series with a simple revision.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is correctly
        labeled and is not sent in reply to the first revision.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
          - [PATCH v2 0/2] A sample series
            - [PATCH v2 1/2] test: Add some lorem ipsum
            - [PATCH v2 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'revision-basic.mbox', [2, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 1])

    def test_threaded_to_cover(self):
        """Series with a revision sent in-reply-to a cover.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is correctly
        labeled but is sent in reply to the cover letter of the first
        revision.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH v2 0/2] A sample series
              - [PATCH v2 1/2] test: Add some lorem ipsum
              - [PATCH v2 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'revision-threaded-to-cover.mbox', [2, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 1])

    def test_threaded_to_patch(self):
        """Series with a revision sent in-reply-to a patch.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is correctly
        labeled but is sent in reply to the second patch of the first
        revision.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
              - [PATCH v2 0/2] A sample series
                - [PATCH v2 1/2] test: Add some lorem ipsum
                - [PATCH v2 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'revision-threaded-to-patch.mbox', [2, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 1])

    def test_out_of_order(self):
        """Series with a revision received out-of-order.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is correctly
        labeled but is sent in reply to the second patch and is
        received out of order.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
                - [PATCH v2 2/2] test: Convert to Markdown
                - [PATCH v2 1/2] test: Add some lorem ipsum
              - [PATCH v2 0/2] A sample series
        """
        covers, patches, _ = self._parse_mbox(
            'revision-out-of-order.mbox', [2, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 1])

    def test_no_cover_letter(self):
        """Series with a revision sent without a cover letter.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is not
        labeled with a series version marker.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'revision-no-cover-letter.mbox', [1, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 0])

    def test_unlabeled(self):
        """Series with a revision sent without a version label.

        Parse a series with a cover letter and two patches, followed by
        a second revision of the same. The second revision is not
        labeled with a series version marker.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'revision-unlabeled.mbox', [2, 4, 0])

        self.assertSerialized(patches, [2, 2])
        self.assertSerialized(covers, [1, 1])

    def test_unnumbered(self):
        """Series with a reply with a diff but no number.

        The random message with the diff should not belong to the
        series, as it lacks a n/N label. We expect 1 series and the
        random message to be orphaned.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - This is an orphaned patch!
        """
        covers, patches, _ = self._parse_mbox(
            'bugs-unnumbered.mbox', [1, 2, 0])

        self.assertEqual(len([p for p in patches if p.latest_series]), 1)
        self.assertEqual(len([p for p in patches if not p.latest_series]), 1)
        self.assertSerialized(covers, [1])

    def test_reply_nocover_noversion(self):
        """Series with a revision sent without a version label or cover
        letter, in reply to earlier version of the same series.

        Parse a series with two patches, followed by a second revision
        of the same. The second revision is not labeled with a series
        version marker.

        This is really, really annoying and people shouldn't do it.

        Input:

            - [PATCH 1/2] test: Add some lorem ipsum
              - [PATCH 2/2] test: Convert to Markdown
                - [PATCH 1/2] test: Add some lorem ipsum
                  - [PATCH 2/2] test: Convert to Markdown

        """
        covers, patches, _ = self._parse_mbox(
            'bugs-nocover-noversion.mbox', [0, 4, 0])

        self.assertSerialized(patches, [2, 2])

    def test_reply_nocover(self):
        """Series with a revision sent in-reply-to a patch, no cover letters.

        Parse a series with two patches, followed by a second revision
        of the same. The second revision is correctly labeled but is
        sent in reply to the second patch of the first revision.

        Input:

          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
              - [PATCH v2 1/2] test: Add some lorem ipsum
                - [PATCH v2 2/2] test: Convert to Markdown

        """
        _, patches, _ = self._parse_mbox(
            'bugs-nocover.mbox', [0, 4, 0])

        self.assertSerialized(patches, [2, 2])


class SeriesTotalTest(_BaseTestCase):

    def test_incomplete(self):
        """Series received with patches missing.

        Parse a series where not all patches were received.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
        """
        covers, patches, _ = self._parse_mbox(
            'base-incomplete.mbox', [1, 1, 0])

        self.assertSerialized(patches, [1])
        self.assertSerialized(covers, [1])

        series = patches[0].latest_series
        self.assertFalse(series.received_all)

    def test_complete(self):
        """Series received with expected number of patches.

        Parse a series where all patches are received as expected.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'base-cover-letter.mbox', [1, 2, 0])

        self.assertSerialized(covers, [1])
        self.assertSerialized(patches, [2])

        series = patches[0].latest_series
        self.assertTrue(series.received_all)

    def test_extra_patches(self):
        """Series received with additional patches.

        Parse a series where an additional patch was later sent.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH 3/n] test: Remove Markdown formatting
        """
        covers, patches, _ = self._parse_mbox(
            'base-extra-patches.mbox', [1, 3, 0])

        self.assertSerialized(covers, [1])
        self.assertSerialized(patches, [3])

        series = patches[0].latest_series
        self.assertTrue(series.received_all)


class SeriesNameTestCase(TestCase):

    def setUp(self):
        self.project = utils.create_project()
        utils.create_state()

    @staticmethod
    def _get_mbox(name):
        """Open an mbox file.

        :param name: Name of mbox file
        """
        return mailbox.mbox(os.path.join(TEST_SERIES_DIR, name))

    def _parse_mail(self, mail):
        return parser.parse_mail(mail, self.project.listid)

    @staticmethod
    def _format_name(cover):
        return cover.name.split(']')[-1]

    def test_cover_letter(self):
        """Cover letter name set as series name.

        Parse a series with a cover letter and two patches and ensure
        the series name is set to the cover letter.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        mbox = self._get_mbox('base-cover-letter.mbox')

        cover = self._parse_mail(mbox[0])
        cover_name = self._format_name(cover)
        self.assertEqual(cover.latest_series.name, cover_name)

        self._parse_mail(mbox[1])
        self.assertEqual(cover.latest_series.name, cover_name)

        self._parse_mail(mbox[2])
        self.assertEqual(cover.latest_series.name, cover_name)

    def test_no_cover_letter(self):
        """Series without a cover letter.

        Parse a series with two patches but no cover letter and ensure
        the series name is set to the first patch's entire subject.

        Input:

          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        mbox = self._get_mbox('base-no-cover-letter.mbox')

        patch = self._parse_mail(mbox[0])
        series = patch.latest_series
        self.assertEqual(series.name, patch.name)

        self._parse_mail(mbox[1])
        self.assertEqual(series.name, patch.name)

    def test_out_of_order(self):
        """Series received out of order.

        Parse a series with a cover letter and two patches that is
        received out of order. Ensure the name is updated as new
        patches are received.

        Input:

            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH 1/2] test: Add some lorem ipsum
          - [PATCH 0/2] A sample series
        """
        mbox = self._get_mbox('base-out-of-order.mbox')

        patch = self._parse_mail(mbox[0])
        self.assertIsNone(patch.latest_series.name)

        patch = self._parse_mail(mbox[1])
        self.assertEqual(patch.latest_series.name, patch.name)

        cover = self._parse_mail(mbox[2])
        self.assertEqual(cover.latest_series.name, self._format_name(cover))

    def test_custom_name(self):
        """Series with custom name.

        Parse a series with a cover letter and two patches that is
        recevied out of order. Ensure a custom name set on the series
        is not overriden by subsequent patches received.

        Input:

            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH 1/2] test: Add some lorem ipsum
          - [PATCH 0/2] A sample series
        """
        mbox = self._get_mbox('base-out-of-order.mbox')

        series = self._parse_mail(mbox[0]).latest_series
        self.assertIsNone(series.name)

        series_name = 'My custom series name'
        series.name = series_name
        series.save()
        self.assertEqual(series.name, series_name)

        self._parse_mail(mbox[1])
        self.assertEqual(series.name, series_name)

        self._parse_mail(mbox[2])
        self.assertEqual(series.name, series_name)
