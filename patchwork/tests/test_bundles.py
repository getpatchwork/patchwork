# Patchwork - automated patch tracking system
# Copyright (C) 2009 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import base64
import datetime
import unittest

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import urlencode

from patchwork.models import Bundle
from patchwork.models import BundlePatch
from patchwork.tests.utils import create_bundle
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user
from patchwork.views import utils as view_utils


def bundle_url(bundle):
    return reverse('bundle-detail', kwargs={
        'username': bundle.owner.username, 'bundlename': bundle.name})


def bundle_mbox_url(bundle):
    return reverse('bundle-mbox', kwargs={
        'username': bundle.owner.username, 'bundlename': bundle.name})


class BundleListTest(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client.login(username=self.user.username,
                          password=self.user.username)

    def test_no_bundles(self):
        response = self.client.get(reverse('user-bundles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['bundles']), 0)

    def test_single_bundle(self):
        bundle = create_bundle(owner=self.user)
        bundle.save()
        response = self.client.get(reverse('user-bundles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['bundles']), 1)


class BundleTestBase(TestCase):

    def setUp(self, count=3):
        self.user = create_user()
        self.client.login(username=self.user.username,
                          password=self.user.username)
        self.bundle = create_bundle(owner=self.user)
        self.project = create_project()
        self.patches = create_patches(count, project=self.project)


class BundleViewTest(BundleTestBase):

    def test_empty_bundle(self):
        response = self.client.get(bundle_url(self.bundle))
        self.assertEqual(response.status_code, 200)
        page = response.context['page']
        self.assertEqual(len(page.object_list), 0)

    def test_non_empty_bundle(self):
        self.bundle.append_patch(self.patches[0])

        response = self.client.get(bundle_url(self.bundle))
        self.assertEqual(response.status_code, 200)
        page = response.context['page']
        self.assertEqual(len(page.object_list), 1)

    def test_bundle_order(self):
        for patch in self.patches:
            self.bundle.append_patch(patch)

        response = self.client.get(bundle_url(self.bundle))

        pos = 0
        for patch in self.patches:
            next_pos = response.content.decode().find(patch.name)
            # ensure that this patch is after the previous
            self.assertTrue(next_pos > pos)
            pos = next_pos

        # reorder and recheck
        i = 0
        for patch in self.patches.__reversed__():
            bundlepatch = BundlePatch.objects.get(bundle=self.bundle,
                                                  patch=patch)
            bundlepatch.order = i
            bundlepatch.save()
            i += 1

        response = self.client.get(bundle_url(self.bundle))
        pos = len(response.content)
        for patch in self.patches:
            next_pos = response.content.decode().find(patch.name)
            # ensure that this patch is now *before* the previous
            self.assertTrue(next_pos < pos)
            pos = next_pos


class BundleMboxTest(BundleTestBase):

    def test_empty_bundle(self):
        response = self.client.get(bundle_mbox_url(self.bundle))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')

    def test_non_empty_bundle(self):
        self.bundle.append_patch(self.patches[0])

        response = self.client.get(bundle_mbox_url(self.bundle))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, b'')


class BundleUpdateTest(BundleTestBase):

    def test_no_action(self):
        newname = 'newbundlename'
        data = {
            'form': 'bundle',
            'name': newname,
            'public': 'on',
        }
        response = self.client.post(bundle_url(self.bundle), data)
        self.assertEqual(response.status_code, 200)

        bundle = Bundle.objects.get(pk=self.bundle.pk)
        self.assertEqual(bundle.name, self.bundle.name)
        self.assertEqual(bundle.public, self.bundle.public)

    def test_update_name(self):
        newname = 'newbundlename'
        data = {
            'form': 'bundle',
            'action': 'update',
            'name': newname,
            'public': '',
        }
        response = self.client.post(bundle_url(self.bundle), data)
        bundle = Bundle.objects.get(pk=self.bundle.pk)
        self.assertRedirects(response, bundle_url(bundle))
        self.assertEqual(bundle.name, newname)
        self.assertEqual(bundle.public, self.bundle.public)

    def test_update_public(self):
        data = {
            'form': 'bundle',
            'action': 'update',
            'name': self.bundle.name,
            'public': 'on',
        }
        response = self.client.post(bundle_url(self.bundle), data)
        self.assertEqual(response.status_code, 200)
        bundle = Bundle.objects.get(pk=self.bundle.pk)
        self.assertEqual(bundle.name, self.bundle.name)
        self.assertEqual(bundle.public, not self.bundle.public)

        # check other forms for errors
        formname = 'patchform'
        if formname not in response.context:
            return
        form = response.context[formname]
        if not form:
            return
        self.assertEqual(form.errors, {})


class BundleMaintainerUpdateTest(BundleUpdateTest):

    def setUp(self):
        super(BundleMaintainerUpdateTest, self).setUp()

        profile = self.user.profile
        profile.maintainer_projects.add(self.project)
        profile.save()


class BundlePublicViewTest(BundleTestBase):

    def setUp(self):
        super(BundlePublicViewTest, self).setUp()
        self.client.logout()
        self.bundle.append_patch(self.patches[0])
        self.url = bundle_url(self.bundle)

    def test_public_bundle(self):
        self.bundle.public = True
        self.bundle.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patches[0].name)

    def test_private_bundle(self):
        self.bundle.public = False
        self.bundle.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class BundlePublicViewMboxTest(BundlePublicViewTest):

    def setUp(self):
        super(BundlePublicViewMboxTest, self).setUp()
        self.url = reverse('bundle-mbox', kwargs={
            'username': self.bundle.owner.username,
            'bundlename': self.bundle.name})


class BundlePublicModifyTest(BundleTestBase):

    """Ensure that non-owners can't modify bundles"""

    def setUp(self):
        super(BundlePublicModifyTest, self).setUp()
        self.bundle.public = True
        self.bundle.save()
        self.other_user = create_user()

    def test_bundle_form_presence(self):
        """Check for presence of the modify form on the bundle"""
        self.client.login(username=self.other_user.username,
                          password=self.other_user.username)
        response = self.client.get(bundle_url(self.bundle))
        self.assertNotContains(response, 'name="form" value="bundle"')
        self.assertNotContains(response, 'Change order')

    def test_bundle_form_submission(self):
        oldname = 'oldbundlename'
        newname = 'newbundlename'
        data = {
            'form': 'bundle',
            'action': 'update',
            'name': newname,
        }
        self.bundle.name = oldname
        self.bundle.save()

        # first, check that we can modify with the owner
        self.client.login(username=self.user.username,
                          password=self.user.username)
        self.client.post(bundle_url(self.bundle), data)
        self.bundle = Bundle.objects.get(pk=self.bundle.pk)
        self.assertEqual(self.bundle.name, newname)

        # reset bundle name
        self.bundle.name = oldname
        self.bundle.save()

        # log in with a different user, and check that we can no longer modify
        self.client.login(username=self.other_user.username,
                          password=self.other_user.username)
        self.client.post(bundle_url(self.bundle), data)
        self.bundle = Bundle.objects.get(pk=self.bundle.pk)
        self.assertNotEqual(self.bundle.name, newname)


class BundlePrivateViewTest(BundleTestBase):

    """Ensure that non-owners can't view private bundles"""

    def setUp(self):
        super(BundlePrivateViewTest, self).setUp()
        self.bundle.public = False
        self.bundle.save()
        self.bundle.append_patch(self.patches[0])
        self.url = bundle_url(self.bundle)
        self.other_user = create_user()

    def test_private_bundle(self):
        # Check we can view as owner
        self.client.login(username=self.user.username,
                          password=self.user.username)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patches[0].name)

        # Check we can't view as another user
        self.client.login(username=self.other_user.username,
                          password=self.other_user.username)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class BundlePrivateViewMboxTest(BundlePrivateViewTest):

    """Ensure that non-owners can't view private bundle mboxes"""

    def setUp(self):
        super(BundlePrivateViewMboxTest, self).setUp()
        self.url = reverse('bundle-mbox', kwargs={
            'username': self.bundle.owner.username,
            'bundlename': self.bundle.name})

    def test_private_bundle_mbox_basic_auth(self):
        self.client.logout()

        def _get_auth_string(user):
            return 'Basic ' + base64.b64encode(b':'.join((
                user.username.encode(),
                user.username.encode()))
            ).strip().decode()

        # Check we can view as owner
        auth_string = _get_auth_string(self.user)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth_string)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patches[0].name)

        # Check we can't view as another user
        auth_string = _get_auth_string(self.other_user)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(response.status_code, 404)

    def test_private_bundle_mbox_token_auth(self):
        self.client.logout()

        # create tokens for both users
        for user in [self.user, self.other_user]:
            view_utils.regenerate_token(user)

        def _get_auth_string(user):
            return 'Token {}'.format(str(user.profile.token))

        # Check we can view as owner
        auth_string = _get_auth_string(self.user)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth_string)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patches[0].name)

        # Check we can't view as another user
        auth_string = _get_auth_string(self.other_user)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(response.status_code, 404)


class BundleCreateFromListTest(BundleTestBase):

    def test_create_empty_bundle(self):
        newbundlename = 'testbundle-new'
        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': self.project.id}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertContains(response, 'Bundle %s created' % newbundlename)

    def test_create_non_empty_bundle(self):
        newbundlename = 'testbundle-new'
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': self.project.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'added to bundle %s' % newbundlename,
                            count=1)

        bundle = Bundle.objects.get(name=newbundlename)
        self.assertEqual(bundle.patches.count(), 1)
        self.assertEqual(bundle.patches.all()[0], patch)

    def test_create_non_empty_bundle_empty_name(self):
        patch = self.patches[0]

        n_bundles = Bundle.objects.count()

        params = {'form': 'patchlistform',
                  'bundle_name': '',
                  'action': 'Create',
                  'project': self.project.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertContains(response, 'No bundle name was specified',
                            status_code=200)

        # test that no new bundles are present
        self.assertEqual(n_bundles, Bundle.objects.count())

    def test_create_duplicate_name(self):
        newbundlename = 'testbundle-dup'
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': self.project.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        n_bundles = Bundle.objects.count()
        self.assertContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'added to bundle %s' % newbundlename,
                            count=1)

        bundle = Bundle.objects.get(name=newbundlename)
        self.assertEqual(bundle.patches.count(), 1)
        self.assertEqual(bundle.patches.all()[0], patch)

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertNotContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'You already have a bundle called')
        self.assertEqual(Bundle.objects.count(), n_bundles)
        self.assertEqual(bundle.patches.count(), 1)


class BundleCreateFromPatchTest(BundleTestBase):

    def test_create_non_empty_bundle(self):
        newbundlename = 'testbundle-new'
        patch = self.patches[0]

        params = {'name': newbundlename,
                  'action': 'createbundle'}

        response = self.client.post(
            reverse('patch-detail',
                    kwargs={'project_id': patch.project.linkname,
                            'msgid': patch.url_msgid}), params)

        self.assertContains(response,
                            'Bundle %s created' % newbundlename)

        bundle = Bundle.objects.get(name=newbundlename)
        self.assertEqual(bundle.patches.count(), 1)
        self.assertEqual(bundle.patches.all()[0], patch)

    def test_create_with_existing_name(self):
        newbundlename = self.bundle.name
        patch = self.patches[0]

        params = {'name': newbundlename,
                  'action': 'createbundle'}

        response = self.client.post(
            reverse('patch-detail',
                    kwargs={'project_id': patch.project.linkname,
                            'msgid': patch.url_msgid}), params)

        self.assertContains(
            response,
            'A bundle called %s already exists' % newbundlename)

        self.assertEqual(Bundle.objects.count(), 1)


class BundleAddFromListTest(BundleTestBase):

    def test_add_to_empty_bundle(self):
        patch = self.patches[0]
        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': self.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertContains(response, 'added to bundle %s' % self.bundle.name,
                            count=1)

        self.assertEqual(self.bundle.patches.count(), 1)
        self.assertEqual(self.bundle.patches.all()[0], patch)

    def test_add_to_non_empty_bundle(self):
        self.bundle.append_patch(self.patches[0])
        patch = self.patches[1]
        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': self.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        self.assertContains(response, 'added to bundle %s' % self.bundle.name,
                            count=1)

        self.assertEqual(self.bundle.patches.count(), 2)
        self.assertIn(self.patches[0], self.bundle.patches.all())
        self.assertIn(self.patches[1], self.bundle.patches.all())

        # check order
        bps = [BundlePatch.objects.get(bundle=self.bundle,
                                       patch=self.patches[i])
               for i in [0, 1]]
        self.assertTrue(bps[0].order < bps[1].order)

    def test_add_duplicate(self):
        self.bundle.append_patch(self.patches[0])
        count = self.bundle.patches.count()
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': self.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        expected = escape(f"Patch '{patch.name}' already in bundle")
        self.assertContains(response, expected, count=1, status_code=200)

        self.assertEqual(count, self.bundle.patches.count())

    def test_add_new_and_duplicate(self):
        self.bundle.append_patch(self.patches[0])
        count = self.bundle.patches.count()
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': self.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked',
                  'patch_id:%d' % self.patches[1].id: 'checked'}

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            params)

        for expected in (
            escape(f"Patch '{patch.name}' already in bundle"),
            escape(f"Patch '{self.patches[1].name}' added to bundle"),
        ):
            self.assertContains(response, expected, count=1, status_code=200)

        self.assertEqual(count + 1, self.bundle.patches.count())


class BundleAddFromPatchTest(BundleTestBase):

    def test_add_to_empty_bundle(self):
        patch = self.patches[0]
        params = {'action': 'addtobundle',
                  'bundle_id': self.bundle.id}

        response = self.client.post(
            reverse('patch-detail',
                    kwargs={'project_id': patch.project.linkname,
                            'msgid': patch.url_msgid}), params)

        self.assertContains(
            response,
            'added to bundle &quot;%s&quot;' % self.bundle.name,
            count=1)

        self.assertEqual(self.bundle.patches.count(), 1)
        self.assertEqual(self.bundle.patches.all()[0], patch)

    def test_add_to_non_empty_bundle(self):
        self.bundle.append_patch(self.patches[0])
        patch = self.patches[1]
        params = {'action': 'addtobundle',
                  'bundle_id': self.bundle.id}

        response = self.client.post(
            reverse('patch-detail',
                    kwargs={'project_id': patch.project.linkname,
                            'msgid': patch.url_msgid}), params)

        self.assertContains(
            response,
            'added to bundle &quot;%s&quot;' % self.bundle.name,
            count=1)

        self.assertEqual(self.bundle.patches.count(), 2)
        self.assertIn(self.patches[0], self.bundle.patches.all())
        self.assertIn(self.patches[1], self.bundle.patches.all())

        # check order
        bps = [BundlePatch.objects.get(bundle=self.bundle,
                                       patch=self.patches[i])
               for i in [0, 1]]
        self.assertTrue(bps[0].order < bps[1].order)


class BundleInitialOrderTest(BundleTestBase):

    """When creating bundles from a patch list, ensure that the patches in the
       bundle are ordered by date"""

    def setUp(self):
        super(BundleInitialOrderTest, self).setUp(5)

        # put patches in an arbitrary order
        idxs = [2, 4, 3, 1, 0]
        self.patches = [self.patches[i] for i in idxs]

        # set dates to be sequential
        last_patch = self.patches[0]
        for patch in self.patches[1:]:
            patch.date = last_patch.date + datetime.timedelta(0, 1)
            patch.save()
            last_patch = patch

    def _test_order(self, ids, expected_order):
        newbundlename = 'testbundle-new'

        # need to define our querystring explicity to enforce ordering
        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': self.project.id,
                  }

        data = urlencode(params) + \
            ''.join(['&patch_id:%d=checked' % i for i in ids])

        response = self.client.post(
            reverse('patch-list', kwargs={
                'project_id': self.project.linkname}),
            data=data,
            content_type='application/x-www-form-urlencoded',
        )

        self.assertContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'added to bundle %s' % newbundlename,
                            count=5)

        bundle = Bundle.objects.get(name=newbundlename)

        # BundlePatches should be sorted by .order by default
        bps = BundlePatch.objects.filter(bundle=bundle)

        for (bp, p) in zip(bps, expected_order):
            self.assertEqual(bp.patch.pk, p.pk)

        bundle.delete()

    def test_bundle_forward_order(self):
        ids = [p.id for p in self.patches]
        self._test_order(ids, self.patches)

    def test_bundle_reverse_order(self):
        ids = [p.id for p in self.patches]
        ids.reverse()
        self._test_order(ids, self.patches)


class BundleReorderTest(BundleTestBase):

    def setUp(self):
        super(BundleReorderTest, self).setUp(5)
        for i in range(5):
            self.bundle.append_patch(self.patches[i])

    def check_reordering(self, neworder, start, end):
        neworder_ids = [self.patches[i].id for i in neworder]

        firstpatch = BundlePatch.objects.get(bundle=self.bundle,
                                             patch=self.patches[start]).patch

        slice_ids = neworder_ids[start:end]
        params = {'form': 'reorderform',
                  'order_start': firstpatch.id,
                  'neworder': slice_ids}

        response = self.client.post(bundle_url(self.bundle), params)

        self.assertEqual(response.status_code, 200)

        bps = BundlePatch.objects.filter(bundle=self.bundle).order_by('order')

        # check if patch IDs are in the expected order:
        bundle_ids = [bp.patch.id for bp in bps]
        self.assertEqual(neworder_ids, bundle_ids)

        # check if order field is still sequential:
        order_numbers = [bp.order for bp in bps]
        # [1 ... len(neworder)]
        expected_order = list(range(1, len(neworder) + 1))
        self.assertEqual(order_numbers, expected_order)

    def test_bundle_reorder_all(self):
        """Reorder all patches."""
        self.check_reordering([2, 1, 4, 0, 3], 0, 5)

    def test_bundle_reorder_end(self):
        """Reorder only the last three patches."""
        self.check_reordering([0, 1, 3, 2, 4], 2, 5)

    def test_bundle_reorder_begin(self):
        """Reorder only the first three patches."""
        self.check_reordering([2, 0, 1, 3, 4], 0, 3)

    def test_bundle_reorder_middle(self):
        """Reorder only 2nd, 3rd, and 4th patches."""
        self.check_reordering([0, 2, 3, 1, 4], 1, 4)


@unittest.skipUnless(settings.COMPAT_REDIR,
                     'requires compat redirection (use the COMPAT_REDIR '
                     'setting)')
class BundleRedirTest(BundleTestBase):
    """Validate redirection of legacy URLs."""

    def setUp(self):
        super(BundleRedirTest, self).setUp()

    def test_bundle_redir(self):
        response = self.client.get(
            reverse('bundle-redir', kwargs={'bundle_id': self.bundle.id}))
        self.assertRedirects(response, bundle_url(self.bundle))

    def test_mbox_redir(self):
        response = self.client.get(reverse(
            'bundle-mbox-redir', kwargs={'bundle_id': self.bundle.id}))
        self.assertRedirects(response, reverse('bundle-mbox', kwargs={
            'username': self.bundle.owner.username,
            'bundlename': self.bundle.name}))
