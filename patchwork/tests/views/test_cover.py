# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import TestCase
from django.urls import reverse

from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_project


class CoverViewTest(TestCase):

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


class CommentRedirectTest(TestCase):

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
