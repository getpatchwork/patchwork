# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import mailbox
import os

from django.test import TestCase

from patchwork import models
from patchwork import parser
from patchwork.tests import utils
from patchwork.views.utils import patch_to_mbox


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

        mbox = mailbox.mbox(os.path.join(TEST_SERIES_DIR, name), create=False)
        for msg in mbox:
            obj = parser.parse_mail(msg, project.listid)
            if type(obj) == models.Cover:
                results[0].append(obj)
            elif type(obj) == models.Patch:
                results[1].append(obj)
            else:
                results[2].append(obj)
        mbox.close()

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

        # sort this lists by series date so we don't have simple sorting issues
        patches.sort(key=lambda x: x.series.date)

        # sanity checks
        self.assertEqual(series.count(), len(counts))
        self.assertEqual(sum(counts), len(patches))

        # walk through each series, ensuring each indexed patch
        # corresponds to the correct series
        start_idx = 0
        for idx, count in enumerate(counts):
            end_idx = start_idx + count

            for patch in patches[start_idx:end_idx]:
                self.assertEqual(patch.series, series[idx])

                # TODO(stephenfin): Rework this function into two different
                # functions - we're clearly not always testing patches here
                if isinstance(patch, models.Patch):
                    self.assertEqual(series[idx].patches.get(id=patch.id),
                                     patch)
                else:
                    self.assertEqual(series[idx].cover_letter, patch)

            start_idx = end_idx


class BaseSeriesTest(_BaseTestCase):
    """Tests for a series without any revisions."""

    def test_single_patch(self):
        """Series with only a single patch.

        Parse a "series" with only a single patch and no subject prefixes.

        Input:

          - [PATCH] test: Add some lorem ipsum
        """
        _, patches, _ = self._parse_mbox(
            'base-single-patch.mbox', [0, 1, 0])

        self.assertSerialized(patches, [1])

    def test_cover_letter(self):
        """Series with a cover letter.

        Parse a series with a cover letter and two patches.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
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

    def test_deep_threaded(self):
        """Series with deep threading.

        Parse a series with a cover letter and two patches that uses
        deep threading (git-format-patch --thread=deep).

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
              - [PATCH 2/2] test: Convert to Markdown
        """
        covers, patches, _ = self._parse_mbox(
            'base-deep-threaded.mbox', [1, 2, 0])

        self.assertSerialized(patches, [2])
        self.assertSerialized(covers, [1])

    def test_out_of_order(self):
        """Series received out of order.

        Parse a series with a cover letter and two patches that is
        received out of order.

        Input:

            - [PATCH 2/2] test: Convert to Markdown
            - [PATCH 1/2] test: Add some lorem ipsum
          - [PATCH 0/2] A sample series
        """
        covers, patches, _ = self._parse_mbox(
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

    def test_different_versions(self):
        """Series received with different version on cover to patches.

        Input:
          - [PATCH net-next v3 0/4] net: dsa: Multi-CPU ground work (v3)
            - [PATCH 1/4] net: dsa: Remove master_netdev and use
                dst->cpu_dp->netdev
            - [PATCH 2/4] net: dsa: Relocate master ethtool operations
            - [PATCH 3/4] net: dsa: Associate slave network device with CPU
                port
            - [PATCH 4/4] net: dsa: Introduce dsa_get_cpu_port()
        """
        covers, patches, _ = self._parse_mbox(
            'base-different-versions.mbox', [1, 4, 0])

        self.assertSerialized(covers, [1])
        self.assertSerialized(patches, [4])

    def test_multiple_references(self):
        """Series received with multiple reference headers.

        Parse a series with four patches and a cover letter that is received
        with multiple reference headers.

        Input:
          - [PATCH V2 0/4] PM / OPP: Minor cleanups
            - [PATCH V2 1/4] PM / OPP: Reorganize _generic_set_opp_regulator()
            - [PATCH V2 2/4] PM / OPP: Don't create copy of regulators
                unnecessarily
            - PATCH V2 3/4] PM / OPP: opp-microvolt is not optional if
                regulators are set
            - [PATCH V2 4/4] PM / OPP: Don't create debugfs "supply-0"
                directory unnecessarily
        """
        covers, patches, _ = self._parse_mbox(
            'bugs-multiple-references.mbox', [1, 4, 0])

        self.assertSerialized(covers, [1])
        self.assertSerialized(patches, [4])

    def test_no_references(self):
        """Series received with no reference headers.

        Parse a series with two patches that is received without any
        reference headers.

        Input:
          - [PATCH 1/2] net: ieee802154: remove explicit set skb->sk
          - [PATCH 2/2] net: ieee802154: fix net_device reference release too
        """
        _, patches, _ = self._parse_mbox(
            'base-no-references.mbox', [0, 2, 0])

        self.assertSerialized(patches, [2])

    def test_no_references_no_cover(self):
        """Series received with no reference headers or cover letter.

        Parse a series with a cover letter and two patches that is received
        without any reference headers.

        Input:
          - [PATCH 0/2] powerpc/dlpar: Correct display of hot-add/hot-remove
                CPUs
            - [PATCH 1/2] powerpc/numa: Update CPU topology when VPHN enabled
            - [Patch 2/2]: powerpc/hotplug/mm: Fix hot-add memory node assoc
        """
        covers, patches, _ = self._parse_mbox(
            'base-no-references-no-cover.mbox', [1, 2, 0])

        self.assertSerialized(patches, [2])
        self.assertSerialized(covers, [1])

    def test_multiple_content_types(self):
        """Test what happens when a patch and comment have different
        Content-Type headers."""

        _, patches, _ = self._parse_mbox(
            'bugs-multiple-content-types.mbox', [0, 1, 1])

        patch = patches[0]
        self.assertEqual(patch_to_mbox(patch).count('Content-Type:'), 1)


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

    def test_threaded_to_single_patch(self):
        """Series with a revision sent in-reply-to a single-patch series.

        Parse a series with a single patch, followed by a second revision of
        the same. The second revision is correctly labeled but is sent in reply
        to the original patch.

          - [PATCH] test: Add some lorem ipsum
            - [PATCH v2] test: Add some lorem ipsum
        """
        _, patches, _ = self._parse_mbox(
            'revision-threaded-to-single-patch.mbox', [0, 2, 0])

        self.assertSerialized(patches, [1, 1])

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

    def test_unlabeled_noreferences(self):
        """Series with a revision sent without a version label or
        reference headers.

        Parse a series with two patches, followed by a second revision of the
        same. The second revision is not labeled with a series version marker
        and neither revision contains reference headers. Only the message-ids
        and receipt times vary (by one hour).

        Input:
          - [PATCH 1/2] net: ieee802154: remove explicit set skb->sk
          - [PATCH 2/2] net: ieee802154: fix net_device reference release too
          - [PATCH 1/2] net: ieee802154: remove explicit set skb->sk
          - [PATCH 2/2] net: ieee802154: fix net_device reference release too
        """
        _, patches, _ = self._parse_mbox(
            'revision-unlabeled-noreferences.mbox', [0, 4, 0])

        self.assertSerialized(patches, [2, 2])

    def test_unnumbered(self):
        """Series with a reply with a diff but no number.

        The random message with the diff should not belong to the
        series, as it lacks a n/N label. We expect two series and the
        random message to be assigned its own series.

        Input:

          - [PATCH 0/2] A sample series
            - [PATCH 1/2] test: Add some lorem ipsum
            - This is an orphaned patch!
        """
        covers, patches, _ = self._parse_mbox(
            'bugs-unnumbered.mbox', [1, 2, 0])

        self.assertSerialized(patches, [1, 1])
        self.assertSerialized(covers, [1, 0])

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

    def test_spamming(self):
        """Series submitted multiple times to the mailing list in quick
        succession.

        Parse a series being submitted multiple times in quick succession,
        which prevents our timeboxing from splitting the lists up. This should
        result in multiple separate series.

        Input:

          - [PATCH v2 1/4] Rework tagging infrastructure
          - [PATCH v2 1/4] Rework tagging infrastructure
          - [PATCH v2 1/4] Rework tagging infrastructure
        """
        _, patches, _ = self._parse_mbox(
            'bugs-spamming.mbox', [0, 3, 0])

        self.assertSerialized(patches, [1, 1, 1])

    def test_mixed_versions(self):
        """Series with a revision sent in reply to an incompleted series.

        Parse a series with two patches, one of which has been lost or
        miscategorized, followed by a second revision of the missing patch.
        None of the patches of the second revision should be included in the
        first revision.

          - [PATCH 1/2] test: Add some lorem ipsum
            - [PATCH v2 2/2] test: Convert to Markdown
        """
        _, patches, _ = self._parse_mbox(
            'bugs-mixed-versions.mbox', [0, 2, 0],
        )

        self.assertSerialized(patches, [1, 1])


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

        series = patches[0].series
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

        series = patches[0].series
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

        series = patches[0].series
        self.assertTrue(series.received_all)


class MercurialSeriesTest(_BaseTestCase):
    """Tests for a series without any revisions.

    All patches are generated using hg(1) email, provided via the Patchbomb
    extension.
    """

    def test_cover_letter(self):
        """Series with a cover letter.

        Parse a series with a cover letter and two patches.

        Input:

          - [PATCH 0 of 2] Sample Mercurial patches
            - [PATCH 1 of 2] contrib: fix check-commit to not reject
                commits from `hg sign` and `hg tag`
            - [PATCH 2 of 2] tests: work around FreeBSD's unzip having
                slightly different output
        """
        covers, patches, comments = self._parse_mbox(
            'mercurial-cover-letter.mbox', [1, 2, 0])

        self.assertSerialized(patches, [2])
        self.assertSerialized(covers, [1])

    def test_no_cover_letter(self):
        """Series without a cover letter.

        Parse a series with two patches but no cover letter.

        Input:

          - [PATCH 1 of 2] contrib: fix check-commit to not reject
              commits from `hg sign` and `hg tag`
            - [PATCH 2 of 2] tests: work around FreeBSD's unzip having
                slightly different output
        """
        _, patches, _ = self._parse_mbox(
            'mercurial-no-cover-letter.mbox', [0, 2, 0])

        self.assertSerialized(patches, [2])


class SeriesNameTestCase(TestCase):

    def setUp(self):
        self.project = utils.create_project()
        utils.create_state()

    @staticmethod
    def _get_mbox(name):
        """Open an mbox file.

        :param name: Name of mbox file
        """
        return mailbox.mbox(os.path.join(TEST_SERIES_DIR, name), create=False)

    def _parse_mail(self, mail):
        return parser.parse_mail(mail, self.project.listid)

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
        cover_name = 'A sample series'
        self.assertEqual(cover.series.name, cover_name)

        self._parse_mail(mbox[1])
        self.assertEqual(cover.series.name, cover_name)

        self._parse_mail(mbox[2])
        self.assertEqual(cover.series.name, cover_name)

        mbox.close()

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
        series = patch.series
        self.assertEqual(series.name, patch.name)

        self._parse_mail(mbox[1])
        self.assertEqual(series.name, patch.name)

        mbox.close()

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
        self.assertIsNone(patch.series.name)

        patch = self._parse_mail(mbox[1])
        self.assertEqual(patch.series.name, patch.name)

        cover = self._parse_mail(mbox[2])
        self.assertEqual(cover.series.name, 'A sample series')

        mbox.close()

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

        series = self._parse_mail(mbox[0]).series
        self.assertIsNone(series.name)

        series_name = 'My custom series name'
        series.name = series_name
        series.save()
        self.assertEqual(series.name, series_name)

        self._parse_mail(mbox[1])
        self.assertEqual(series.name, series_name)

        self._parse_mail(mbox[2])
        self.assertEqual(series.name, series_name)

        mbox.close()
