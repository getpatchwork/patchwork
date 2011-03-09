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
import datetime
from django.test import TestCase
from django.test.client import Client
from django.utils.http import urlencode
from patchwork.models import Patch, Bundle, BundlePatch, Person
from patchwork.tests.utils import defaults, create_user, find_in_context

class BundleListTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.login(username = self.user.username,
                password = self.user.username)

    def testNoBundles(self):
        response = self.client.get('/user/bundles/')
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(
                len(find_in_context(response.context, 'bundles')), 0)

    def testSingleBundle(self):
        defaults.project.save()
        bundle = Bundle(owner = self.user, project = defaults.project)
        bundle.save()
        response = self.client.get('/user/bundles/')
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(
                len(find_in_context(response.context, 'bundles')), 1)

    def tearDown(self):
        self.user.delete()

class BundleTestBase(TestCase):
    def setUp(self, patch_count=3):
        patch_names = ['testpatch%d' % (i) for i in range(1, patch_count+1)]
        self.user = create_user()
        self.client.login(username = self.user.username,
                password = self.user.username)
        defaults.project.save()
        self.bundle = Bundle(owner = self.user, project = defaults.project,
                name = 'testbundle')
        self.bundle.save()
        self.patches = []

        for patch_name in patch_names:
            patch = Patch(project = defaults.project,
                               msgid = patch_name, name = patch_name,
                               submitter = Person.objects.get(user = self.user),
                               content = '')
            patch.save()
            self.patches.append(patch)

    def tearDown(self):
        for patch in self.patches:
            patch.delete()
        self.bundle.delete()
        self.user.delete()

class BundleViewTest(BundleTestBase):

    def testEmptyBundle(self):
        response = self.client.get('/user/bundle/%d/' % self.bundle.id)
        self.failUnlessEqual(response.status_code, 200)
        page = find_in_context(response.context, 'page')
        self.failUnlessEqual(len(page.object_list), 0)

    def testNonEmptyBundle(self):
        self.bundle.append_patch(self.patches[0])

        response = self.client.get('/user/bundle/%d/' % self.bundle.id)
        self.failUnlessEqual(response.status_code, 200)
        page = find_in_context(response.context, 'page')
        self.failUnlessEqual(len(page.object_list), 1)

    def testBundleOrder(self):
        for patch in self.patches:
            self.bundle.append_patch(patch)

        response = self.client.get('/user/bundle/%d/' % self.bundle.id)

        pos = 0
        for patch in self.patches:
            next_pos = response.content.find(patch.name)
            # ensure that this patch is after the previous
            self.failUnless(next_pos > pos)
            pos = next_pos

        # reorder and recheck
        i = 0
        for patch in self.patches.__reversed__():
            bundlepatch = BundlePatch.objects.get(bundle = self.bundle,
                    patch = patch)
            bundlepatch.order = i
            bundlepatch.save()
            i += 1

        response = self.client.get('/user/bundle/%d/' % self.bundle.id)
        pos = len(response.content)
        for patch in self.patches:
            next_pos = response.content.find(patch.name)
            # ensure that this patch is now *before* the previous
            self.failUnless(next_pos < pos)
            pos = next_pos

class BundleCreateFromListTest(BundleTestBase):
    def testCreateEmptyBundle(self):
        newbundlename = 'testbundle-new'
        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': defaults.project.id}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'Bundle %s created' % newbundlename)

    def testCreateNonEmptyBundle(self):
        newbundlename = 'testbundle-new'
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': defaults.project.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'added to bundle %s' % newbundlename,
            count = 1)

        bundle = Bundle.objects.get(name = newbundlename)
        self.failUnlessEqual(bundle.patches.count(), 1)
        self.failUnlessEqual(bundle.patches.all()[0], patch)

    def testCreateNonEmptyBundleEmptyName(self):
        newbundlename = 'testbundle-new'
        patch = self.patches[0]

        n_bundles = Bundle.objects.count()

        params = {'form': 'patchlistform',
                  'bundle_name': '',
                  'action': 'Create',
                  'project': defaults.project.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'No bundle name was specified',
                status_code = 200)

        # test that no new bundles are present
        self.failUnlessEqual(n_bundles, Bundle.objects.count())

class BundleCreateFromPatchTest(BundleTestBase):
    def testCreateNonEmptyBundle(self):
        newbundlename = 'testbundle-new'
        patch = self.patches[0]

        params = {'name': newbundlename,
                  'action': 'createbundle'}

        response = self.client.post('/patch/%d/' % patch.id, params)

        self.assertContains(response,
                'Bundle %s created' % newbundlename)

        bundle = Bundle.objects.get(name = newbundlename)
        self.failUnlessEqual(bundle.patches.count(), 1)
        self.failUnlessEqual(bundle.patches.all()[0], patch)

    def testCreateWithExistingName(self):
        newbundlename = self.bundle.name
        patch = self.patches[0]

        params = {'name': newbundlename,
                  'action': 'createbundle'}

        response = self.client.post('/patch/%d/' % patch.id, params)

        self.assertContains(response,
                'A bundle called %s already exists' % newbundlename)

        count = Bundle.objects.count()
        self.failUnlessEqual(Bundle.objects.count(), 1)

class BundleAddFromListTest(BundleTestBase):
    def testAddToEmptyBundle(self):
        patch = self.patches[0]
        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': defaults.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'added to bundle %s' % self.bundle.name,
            count = 1)

        self.failUnlessEqual(self.bundle.patches.count(), 1)
        self.failUnlessEqual(self.bundle.patches.all()[0], patch)

    def testAddToNonEmptyBundle(self):
        self.bundle.append_patch(self.patches[0])
        patch = self.patches[1]
        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': defaults.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'added to bundle %s' % self.bundle.name,
            count = 1)

        self.failUnlessEqual(self.bundle.patches.count(), 2)
        self.failUnless(self.patches[0] in self.bundle.patches.all())
        self.failUnless(self.patches[1] in self.bundle.patches.all())

        # check order
        bps = [ BundlePatch.objects.get(bundle = self.bundle,
                                        patch = self.patches[i]) \
                for i in [0, 1] ]
        self.failUnless(bps[0].order < bps[1].order)

    def testAddDuplicate(self):
        self.bundle.append_patch(self.patches[0])
        count = self.bundle.patches.count()
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': defaults.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'Patch &#39;%s&#39; already in bundle' \
                            % patch.name, count = 1, status_code = 200)

        self.assertEquals(count, self.bundle.patches.count())

    def testAddNewAndDuplicate(self):
        self.bundle.append_patch(self.patches[0])
        count = self.bundle.patches.count()
        patch = self.patches[0]

        params = {'form': 'patchlistform',
                  'action': 'Add',
                  'project': defaults.project.id,
                  'bundle_id': self.bundle.id,
                  'patch_id:%d' % patch.id: 'checked',
                  'patch_id:%d' % self.patches[1].id: 'checked'}

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                params)

        self.assertContains(response, 'Patch &#39;%s&#39; already in bundle' \
                            % patch.name, count = 1, status_code = 200)
        self.assertContains(response, 'Patch &#39;%s&#39; added to bundle' \
                            % self.patches[1].name, count = 1,
                            status_code = 200)
        self.assertEquals(count + 1, self.bundle.patches.count())

class BundleAddFromPatchTest(BundleTestBase):
    def testAddToEmptyBundle(self):
        patch = self.patches[0]
        params = {'action': 'addtobundle',
                  'bundle_id': self.bundle.id}

        response = self.client.post('/patch/%d/' % patch.id, params)

        self.assertContains(response,
                'added to bundle &quot;%s&quot;' % self.bundle.name,
                count = 1)

        self.failUnlessEqual(self.bundle.patches.count(), 1)
        self.failUnlessEqual(self.bundle.patches.all()[0], patch)

    def testAddToNonEmptyBundle(self):
        self.bundle.append_patch(self.patches[0])
        patch = self.patches[1]
        params = {'action': 'addtobundle',
                  'bundle_id': self.bundle.id}

        response = self.client.post('/patch/%d/' % patch.id, params)

        self.assertContains(response,
                'added to bundle &quot;%s&quot;' % self.bundle.name,
                count = 1)

        self.failUnlessEqual(self.bundle.patches.count(), 2)
        self.failUnless(self.patches[0] in self.bundle.patches.all())
        self.failUnless(self.patches[1] in self.bundle.patches.all())

        # check order
        bps = [ BundlePatch.objects.get(bundle = self.bundle,
                                        patch = self.patches[i]) \
                for i in [0, 1] ]
        self.failUnless(bps[0].order < bps[1].order)

class BundleInitialOrderTest(BundleTestBase):
    """When creating bundles from a patch list, ensure that the patches in the
       bundle are ordered by date"""

    def setUp(self):
        super(BundleInitialOrderTest, self).setUp(5)

        # put patches in an arbitrary order
        idxs = [2, 4, 3, 1, 0]
        self.patches = [ self.patches[i] for i in idxs ]

        # set dates to be sequential
        last_patch = self.patches[0]
        for patch in self.patches[1:]:
            patch.date = last_patch.date + datetime.timedelta(0, 1)
            patch.save()
            last_patch = patch

    def _testOrder(self, ids, expected_order):
        newbundlename = 'testbundle-new'

        # need to define our querystring explicity to enforce ordering
        params = {'form': 'patchlistform',
                  'bundle_name': newbundlename,
                  'action': 'Create',
                  'project': defaults.project.id,
        }

        data = urlencode(params) + \
               ''.join([ '&patch_id:%d=checked' % i for i in ids ])

        response = self.client.post(
                '/project/%s/list/' % defaults.project.linkname,
                data = data,
                content_type = 'application/x-www-form-urlencoded',
                )

        self.assertContains(response, 'Bundle %s created' % newbundlename)
        self.assertContains(response, 'added to bundle %s' % newbundlename,
            count = 5)

        bundle = Bundle.objects.get(name = newbundlename)

        # BundlePatches should be sorted by .order by default
        bps = BundlePatch.objects.filter(bundle = bundle)

        for (bp, p) in zip(bps, expected_order):
            self.assertEqual(bp.patch.pk, p.pk)

        bundle.delete()

    def testBundleForwardOrder(self):
        ids = map(lambda p: p.id, self.patches)
        self._testOrder(ids, self.patches)

    def testBundleReverseOrder(self):
        ids = map(lambda p: p.id, self.patches)
        ids.reverse()
        self._testOrder(ids, self.patches)

class BundleReorderTest(BundleTestBase):
    def setUp(self):
        super(BundleReorderTest, self).setUp(5)
        for i in range(5):
            self.bundle.append_patch(self.patches[i])

    def checkReordering(self, neworder, start, end):
        neworder_ids = [ self.patches[i].id for i in neworder ]

        firstpatch = BundlePatch.objects.get(bundle = self.bundle,
                patch = self.patches[start]).patch

        slice_ids = neworder_ids[start:end]
        params = {'form': 'reorderform',
                  'order_start': firstpatch.id,
                  'neworder': slice_ids}

        response = self.client.post('/user/bundle/%d/' % self.bundle.id,
                                    params)

        self.failUnlessEqual(response.status_code, 200)

        bps = BundlePatch.objects.filter(bundle = self.bundle) \
                        .order_by('order')

        # check if patch IDs are in the expected order:
        bundle_ids = [ bp.patch.id for bp in bps ]
        self.failUnlessEqual(neworder_ids, bundle_ids)

        # check if order field is still sequential:
        order_numbers = [ bp.order for bp in bps ]
        expected_order = range(1, len(neworder)+1) # [1 ... len(neworder)]
        self.failUnlessEqual(order_numbers, expected_order)

    def testBundleReorderAll(self):
        # reorder all patches:
        self.checkReordering([2,1,4,0,3], 0, 5)

    def testBundleReorderEnd(self):
        # reorder only the last three patches
        self.checkReordering([0,1,3,2,4], 2, 5)

    def testBundleReorderBegin(self):
        # reorder only the first three patches
        self.checkReordering([2,0,1,3,4], 0, 3)

    def testBundleReorderMiddle(self):
        # reorder only 2nd, 3rd, and 4th patches
        self.checkReordering([0,2,3,1,4], 1, 4)
