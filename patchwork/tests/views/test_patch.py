# Patchwork - automated patch tracking system
# Copyright (C) 2012 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime as dt
from datetime import timedelta
import re
import unittest

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from patchwork.models import Check
from patchwork.models import Patch
from patchwork.models import State
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user
from patchwork.tests.utils import read_patch


class EmptyPatchListTest(TestCase):

    def test_empty_patch_list(self):
        """Validates absence of table with zero patches."""
        project = create_project()
        url = reverse('patch-list', kwargs={'project_id': project.linkname})
        response = self.client.get(url)
        self.assertContains(response, 'No patches to display')


class PatchListOrderingTest(TestCase):

    patchmeta = [
        ('AlCMyjOsx', 'AlxMyjOsx@nRbqkQV.wBw',
         dt(2014, 3, 16, 13, 4, 50, 155643)),
        ('MMZnrcDjT', 'MMmnrcDjT@qGaIfOl.tbk',
         dt(2014, 1, 25, 13, 4, 50, 162814)),
        ('WGirwRXgK', 'WGSrwRXgK@TriIETY.GhE',
         dt(2014, 2, 14, 13, 4, 50, 169305)),
        ('isjNIuiAc', 'issNIuiAc@OsEirYx.EJh',
         dt(2014, 3, 15, 13, 4, 50, 176264)),
        ('XkAQpYGws', 'XkFQpYGws@hzntTcm.JSE',
         dt(2014, 1, 18, 13, 4, 50, 182493)),
        ('uJuCPWMvi', 'uJACPWMvi@AVRBOBl.ecy',
         dt(2014, 3, 12, 13, 4, 50, 189554)),
        ('TyQmWtcbg', 'TylmWtcbg@DzrNeNH.JuB',
         dt(2014, 2, 3, 13, 4, 50, 195685)),
        ('FpvAhWRdX', 'FpKAhWRdX@agxnCAI.wFO',
         dt(2014, 3, 15, 13, 4, 50, 201398)),
        ('bmoYvnyWa', 'bmdYvnyWa@aeoPnlX.juy',
         dt(2014, 3, 4, 13, 4, 50, 206800)),
        ('CiReUQsAq', 'CiieUQsAq@DnOYRuf.TTI',
         dt(2014, 3, 28, 13, 4, 50, 212169)),
    ]

    def setUp(self):
        self.project = create_project()

        for name, email, date in self.patchmeta:
            person = create_person(name=name, email=email)
            create_patch(submitter=person, project=self.project,
                         date=date)

    def _extract_patch_ids(self, response):
        id_re = re.compile(r'<tr id="patch_row:(\d+)"')
        ids = [int(m.group(1))
               for m in id_re.finditer(response.content.decode())]

        return ids

    def _test_sequence(self, response, test_fn):
        ids = self._extract_patch_ids(response)
        self.assertTrue(bool(ids))
        patches = [Patch.objects.get(id=i) for i in ids]
        pairs = list(zip(patches, patches[1:]))

        for p1, p2 in pairs:
            test_fn(p1, p2)

    def test_date_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=date')

        def test_fn(p1, p2):
            self.assertLessEqual(p1.date, p2.date)

        self._test_sequence(response, test_fn)

    def test_date_reverse_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=-date')

        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.date, p2.date)

        self._test_sequence(response, test_fn)

    # TODO(stephenfin): Looks like this has been resolved in Django 2.1 [1]? If
    # not, it should be possible [2]
    #
    # [1] https://code.djangoproject.com/ticket/30248
    # [2] https://michaelsoolee.com/case-insensitive-sorting-sqlite/
    @unittest.skipIf('sqlite3' in settings.DATABASES['default']['ENGINE'],
                     'The sqlite3 backend does not support case insensitive '
                     'ordering')
    def test_submitter_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=submitter')

        def test_fn(p1, p2):
            self.assertLessEqual(p1.submitter.name.lower(),
                                 p2.submitter.name.lower())

        self._test_sequence(response, test_fn)

    @unittest.skipIf('sqlite3' in settings.DATABASES['default']['ENGINE'],
                     'The sqlite3 backend does not support case insensitive '
                     'ordering')
    def test_submitter_reverse_order(self):
        url = reverse('patch-list',
                      kwargs={'project_id': self.project.linkname})
        response = self.client.get(url + '?order=-submitter')

        def test_fn(p1, p2):
            self.assertGreaterEqual(p1.submitter.name.lower(),
                                    p2.submitter.name.lower())

        self._test_sequence(response, test_fn)


class PatchListFilteringTest(TestCase):

    def test_escaping(self):
        """Validate escaping of filter fragments in a query string.

        Stray ampersands should not get reflected back in the filter
        links.
        """
        project = create_project()
        url = reverse('patch-list', args=[project.linkname])

        response = self.client.get(url + '?submitter=a%%26b=c')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'submitter=a&amp;b=c')
        self.assertNotContains(response, 'submitter=a&b=c')

    def test_utf8_handling(self):
        """Validate handling of non-ascii characters."""
        project = create_project()
        url = reverse('patch-list', args=[project.linkname])

        response = self.client.get(url + '?submitter=%%E2%%98%%83')

        self.assertEqual(response.status_code, 200)


class PatchViewTest(TestCase):

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

    def test_comment_redirect(self):
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


class PatchUpdateTest(TestCase):

    properties_form_id = 'patchform-properties'

    def setUp(self):
        self.project = create_project()
        self.user = create_maintainer(self.project)
        self.patches = create_patches(3, project=self.project)

        self.client.login(username=self.user.username,
                          password=self.user.username)

        self.url = reverse('patch-list', args=[self.project.linkname])
        self.base_data = {
            'action': 'Update',
            'project': str(self.project.id),
            'form': 'patchlistform',
            'archived': '*',
            'delegate': '*',
            'state': '*'
        }

    def _select_all_patches(self, data):
        for patch in self.patches:
            data['patch_id:%d' % patch.id] = 'checked'

    def test_archiving_patches(self):
        data = self.base_data.copy()
        data.update({'archived': 'True'})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, 'No patches to display',
                            status_code=200)
        # Don't use the cached version of patches: retrieve from the DB
        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertTrue(patch.archived)

    def test_unarchiving_patches(self):
        # Start with one patch archived and the remaining ones unarchived.
        self.patches[0].archived = True
        self.patches[0].save()

        data = self.base_data.copy()
        data.update({'archived': 'False'})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id,
                            status_code=200)
        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertFalse(patch.archived)

    def _test_state_change(self, state):
        data = self.base_data.copy()
        data.update({'state': str(state)})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id,
                            status_code=200)
        return response

    def test_state_change_valid(self):
        state = create_state()

        self._test_state_change(state.pk)

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.state, state)

    def test_state_change_invalid(self):
        state = max(State.objects.all().values_list('id', flat=True)) + 1
        orig_states = [patch.state for patch in self.patches]

        response = self._test_state_change(state)

        new_states = [Patch.objects.get(pk=p.pk).state for p in self.patches]
        self.assertEqual(new_states, orig_states)
        self.assertFormError(response, 'patchform', 'state',
                             'Select a valid choice. That choice is not one '
                             'of the available choices.')

    def _test_delegate_change(self, delegate_str):
        data = self.base_data.copy()
        data.update({'delegate': delegate_str})
        self._select_all_patches(data)

        response = self.client.post(self.url, data)

        self.assertContains(response, self.properties_form_id, status_code=200)
        return response

    def test_delegate_change_valid(self):
        delegate = create_maintainer(self.project)

        self._test_delegate_change(str(delegate.pk))

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.delegate, delegate)

    def test_delegate_clear(self):
        self._test_delegate_change('')

        for patch in [Patch.objects.get(pk=p.pk) for p in self.patches]:
            self.assertEqual(patch.delegate, None)


class UTF8PatchViewTest(TestCase):

    def setUp(self):
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(diff=patch_content)

    def test_patch_view(self):
        response = self.client.get(reverse(
            'patch-detail', args=[self.patch.project.linkname,
                                  self.patch.url_msgid]))
        self.assertContains(response, self.patch.name)

    def test_mbox_view(self):
        response = self.client.get(
            reverse('patch-mbox', args=[self.patch.project.linkname,
                                        self.patch.url_msgid]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.patch.diff in response.content.decode('utf-8'))

    def test_raw_view(self):
        response = self.client.get(reverse('patch-raw',
                                           args=[self.patch.project.linkname,
                                                 self.patch.url_msgid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), self.patch.diff)


class UTF8HeaderPatchViewTest(UTF8PatchViewTest):

    def setUp(self):
        author = create_person(name=u'P\xe4tch Author')
        patch_content = read_patch('0002-utf-8.patch', encoding='utf-8')
        self.patch = create_patch(submitter=author, diff=patch_content)
