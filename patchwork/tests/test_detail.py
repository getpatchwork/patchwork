# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from patchwork.models import Check
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user


class CoverViewTest(TestCase):

    def test_redirect(self):
        patch = create_patch()

        requested_url = reverse('cover-detail',
                                kwargs={'project_id': patch.project.linkname,
                                        'msgid': patch.url_msgid})
        redirect_url = reverse('patch-detail',
                               kwargs={'project_id': patch.project.linkname,
                                       'msgid': patch.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_old_detail_url(self):
        cover = create_cover()

        requested_url = reverse('cover-id-redirect',
                                kwargs={'cover_id': cover.id})
        redirect_url = reverse('cover-detail',
                               kwargs={'project_id': cover.project.linkname,
                                       'msgid': cover.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_old_mbox_url(self):
        cover = create_cover()

        requested_url = reverse('cover-mbox-redirect',
                                kwargs={'cover_id': cover.id})
        redirect_url = reverse('cover-mbox',
                               kwargs={'project_id': cover.project.linkname,
                                       'msgid': cover.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_invalid_project_id(self):
        requested_url = reverse(
            'cover-detail',
            kwargs={'project_id': 'foo', 'msgid': 'bar'},
        )
        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_cover_id(self):
        project = create_project()
        requested_url = reverse(
            'cover-detail',
            kwargs={'project_id': project.linkname, 'msgid': 'foo'},
        )
        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 404)


class PatchViewTest(TestCase):

    def test_redirect(self):
        cover = create_cover()

        requested_url = reverse('patch-detail',
                                kwargs={'project_id': cover.project.linkname,
                                        'msgid': cover.url_msgid})
        redirect_url = reverse('cover-detail',
                               kwargs={'project_id': cover.project.linkname,
                                       'msgid': cover.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_old_detail_url(self):
        patch = create_patch()

        requested_url = reverse('patch-id-redirect',
                                kwargs={'patch_id': patch.id})
        redirect_url = reverse('patch-detail',
                               kwargs={'project_id': patch.project.linkname,
                                       'msgid': patch.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_old_mbox_url(self):
        patch = create_patch()

        requested_url = reverse('patch-mbox-redirect',
                                kwargs={'patch_id': patch.id})
        redirect_url = reverse('patch-mbox',
                               kwargs={'project_id': patch.project.linkname,
                                       'msgid': patch.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_old_raw_url(self):
        patch = create_patch()

        requested_url = reverse('patch-raw-redirect',
                                kwargs={'patch_id': patch.id})
        redirect_url = reverse('patch-raw',
                               kwargs={'project_id': patch.project.linkname,
                                       'msgid': patch.url_msgid})

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_escaping(self):
        # Warning: this test doesn't guarantee anything - it only tests some
        # fields
        unescaped_string = 'blah<b>TEST</b>blah'
        patch = create_patch()
        patch.diff = unescaped_string
        patch.commit_ref = unescaped_string
        patch.pull_url = unescaped_string
        patch.name = unescaped_string
        patch.msgid = '<' + unescaped_string + '>'
        patch.headers = unescaped_string
        patch.content = unescaped_string
        patch.save()
        requested_url = reverse('patch-detail',
                                kwargs={'project_id': patch.project.linkname,
                                        'msgid': patch.url_msgid})
        response = self.client.get(requested_url)
        self.assertNotIn('<b>TEST</b>'.encode('utf-8'), response.content)

    def test_invalid_project_id(self):
        requested_url = reverse(
            'patch-detail',
            kwargs={'project_id': 'foo', 'msgid': 'bar'},
        )
        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_patch_id(self):
        project = create_project()
        requested_url = reverse(
            'patch-detail',
            kwargs={'project_id': project.linkname, 'msgid': 'foo'},
        )
        response = self.client.get(requested_url)
        self.assertEqual(response.status_code, 404)

    def test_patch_with_checks(self):
        user = create_user()
        patch = create_patch()
        check_a = create_check(
            patch=patch, user=user, context='foo', state=Check.STATE_FAIL,
            date=(dt.utcnow() - timedelta(days=1)))
        create_check(
            patch=patch, user=user, context='foo', state=Check.STATE_SUCCESS)
        check_b = create_check(
            patch=patch, user=user, context='bar', state=Check.STATE_PENDING)
        requested_url = reverse(
            'patch-detail',
            kwargs={
                'project_id': patch.project.linkname,
                'msgid': patch.url_msgid,
            },
        )
        response = self.client.get(requested_url)

        # the response should contain checks
        self.assertContains(response, '<h2>Checks</h2>')

        # and it should only show the unique checks
        self.assertEqual(
            1, response.content.decode().count(
                f'<td>{check_a.user}/{check_a.context}</td>'
            ))
        self.assertEqual(
            1, response.content.decode().count(
                f'<td>{check_b.user}/{check_b.context}</td>'
            ))


class CommentRedirectTest(TestCase):

    def test_patch_redirect(self):
        patch = create_patch()
        comment_id = create_patch_comment(patch=patch).id

        requested_url = reverse('comment-redirect',
                                kwargs={'comment_id': comment_id})
        redirect_url = '%s#%d' % (
            reverse('patch-detail',
                    kwargs={'project_id': patch.project.linkname,
                            'msgid': patch.url_msgid}),
            comment_id)

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)

    def test_cover_redirect(self):
        cover = create_cover()
        comment_id = create_cover_comment(cover=cover).id

        requested_url = reverse('comment-redirect',
                                kwargs={'comment_id': comment_id})
        redirect_url = '%s#%d' % (
            reverse('cover-detail',
                    kwargs={'project_id': cover.project.linkname,
                            'msgid': cover.url_msgid}),
            comment_id)

        response = self.client.get(requested_url)
        self.assertRedirects(response, redirect_url)
