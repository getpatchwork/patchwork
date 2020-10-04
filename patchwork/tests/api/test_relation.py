# Patchwork - automated patch tracking system
# Copyright (C) 2020, IBM Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from django.conf import settings
from django.urls import reverse

from patchwork.models import Patch
from patchwork.models import PatchRelation
from patchwork.tests.api import utils
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patches
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_relation
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestRelationSimpleAPI(utils.APITestCase):
    @staticmethod
    def api_url(item=None, version=None):
        kwargs = {}
        if version:
            kwargs['version'] = version

        if item is None:
            return reverse('api-patch-list', kwargs=kwargs)
        kwargs['pk'] = item
        return reverse('api-patch-detail', kwargs=kwargs)

    def setUp(self):
        self.project = create_project()
        self.normal_user = create_user()
        self.maintainer = create_maintainer(self.project)

    def test_no_relation(self):
        patch = create_patch(project=self.project)
        resp = self.client.get(self.api_url(item=patch.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['related'], [])

    @utils.store_samples('relation-list')
    def test_list_two_patch_relation(self):
        relation = create_relation()
        patches = create_patches(2, project=self.project, related=relation)

        # nobody
        resp = self.client.get(self.api_url(item=patches[0].pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('related', resp.data)
        self.assertEqual(len(resp.data['related']), 1)
        self.assertEqual(resp.data['related'][0]['id'], patches[1].pk)

        resp = self.client.get(self.api_url(item=patches[1].pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('related', resp.data)
        self.assertEqual(len(resp.data['related']), 1)
        self.assertEqual(resp.data['related'][0]['id'], patches[0].pk)

    @utils.store_samples('relation-create-forbidden')
    def test_create_two_patch_relation_nobody(self):
        patches = create_patches(2, project=self.project)

        resp = self.client.patch(
            self.api_url(item=patches[0].pk), {'related': [patches[1].pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_two_patch_relation_user(self):
        patches = create_patches(2, project=self.project)

        self.client.force_authenticate(user=self.normal_user)
        resp = self.client.patch(
            self.api_url(item=patches[0].pk), {'related': [patches[1].pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @utils.store_samples('relation-create-maintainer')
    def test_create_two_patch_relation_maintainer(self):
        patches = create_patches(2, project=self.project)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=patches[0].pk), {'related': [patches[1].pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # reload and verify
        patches = Patch.objects.all()
        self.assertIsNotNone(patches[0].related)
        self.assertIsNotNone(patches[1].related)
        self.assertEqual(patches[1].related, patches[0].related)

    def test_delete_two_patch_relation_nobody(self):
        relation = create_relation()
        patch = create_patches(2, project=self.project, related=relation)[0]

        self.assertEqual(PatchRelation.objects.count(), 1)

        resp = self.client.patch(self.api_url(item=patch.pk), {'related': []})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PatchRelation.objects.count(), 1)

    @utils.store_samples('relation-delete')
    def test_delete_two_patch_relation_maintainer(self):
        relation = create_relation()
        patch = create_patches(2, project=self.project, related=relation)[0]

        self.assertEqual(PatchRelation.objects.count(), 1)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(self.api_url(item=patch.pk), {'related': []})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(PatchRelation.objects.count(), 0)
        self.assertEqual(
            Patch.objects.filter(related__isnull=False).exists(), False
        )

    def test_create_three_patch_relation(self):
        patches = create_patches(3, project=self.project)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=patches[0].pk),
            {'related': [patches[1].pk, patches[2].pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # reload and verify
        patches = Patch.objects.all()
        self.assertIsNotNone(patches[0].related)
        self.assertIsNotNone(patches[1].related)
        self.assertIsNotNone(patches[2].related)
        self.assertEqual(patches[0].related, patches[1].related)
        self.assertEqual(patches[1].related, patches[2].related)

    def test_delete_from_three_patch_relation(self):
        relation = create_relation()
        patch = create_patches(3, project=self.project, related=relation)[0]

        self.assertEqual(PatchRelation.objects.count(), 1)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(self.api_url(item=patch.pk), {'related': []})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(Patch.objects.get(id=patch.pk).related)
        self.assertEqual(PatchRelation.objects.count(), 1)
        self.assertEqual(PatchRelation.objects.first().patches.count(), 2)

    @utils.store_samples('relation-extend-through-new')
    def test_extend_relation_through_new(self):
        relation = create_relation()
        existing_patch_a = create_patches(
            2, project=self.project, related=relation)[0]

        new_patch = create_patch(project=self.project)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=new_patch.pk), {'related': [existing_patch_a.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(relation, Patch.objects.get(pk=new_patch.pk).related)
        self.assertEqual(relation.patches.count(), 3)

    def test_extend_relation_through_old(self):
        relation = create_relation()
        existing_patch_a = create_patches(
            2, project=self.project, related=relation)[0]

        new_patch = create_patch(project=self.project)

        # maintainer
        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=existing_patch_a.pk), {'related': [new_patch.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(relation, Patch.objects.get(id=new_patch.id).related)
        self.assertEqual(relation.patches.count(), 3)

    def test_extend_relation_through_new_two(self):
        relation = create_relation()
        existing_patch_a = create_patches(
            2, project=self.project, related=relation)[0]

        new_patch_a = create_patch(project=self.project)
        new_patch_b = create_patch(project=self.project)

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=new_patch_a.pk),
            {'related': [existing_patch_a.pk, new_patch_b.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            relation, Patch.objects.get(id=new_patch_a.id).related
        )
        self.assertEqual(
            relation, Patch.objects.get(id=new_patch_b.id).related
        )
        self.assertEqual(relation.patches.count(), 4)

    @utils.store_samples('relation-extend-through-old')
    def test_extend_relation_through_old_two(self):
        relation = create_relation()
        existing_patch_a = create_patches(
            2, project=self.project, related=relation)[0]

        new_patch_a = create_patch(project=self.project)
        new_patch_b = create_patch(project=self.project)

        # maintainer
        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=existing_patch_a.pk),
            {'related': [new_patch_a.pk, new_patch_b.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            relation, Patch.objects.get(id=new_patch_a.id).related
        )
        self.assertEqual(
            relation, Patch.objects.get(id=new_patch_b.id).related
        )
        self.assertEqual(relation.patches.count(), 4)

    def test_remove_one_patch_from_relation_bad(self):
        relation = create_relation()
        patches = create_patches(3, project=self.project, related=relation)
        keep_patch_a = patches[1]
        keep_patch_b = patches[1]

        # this should do nothing - it is interpreted as
        # _adding_ keep_patch_b again which is a no-op.

        # maintainer
        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=keep_patch_a.pk), {'related': [keep_patch_b.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(relation.patches.count(), 3)

    def test_remove_one_patch_from_relation_good(self):
        relation = create_relation()
        target_patch = create_patches(
            3, project=self.project, related=relation)[0]

        # maintainer
        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=target_patch.pk), {'related': []}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(Patch.objects.get(id=target_patch.id).related)
        self.assertEqual(relation.patches.count(), 2)

    @utils.store_samples('relation-forbid-moving-between-relations')
    def test_forbid_moving_patch_between_relations(self):
        """Test the break-before-make logic"""
        relation_a = create_relation()
        create_patches(2, project=self.project, related=relation_a)
        relation_b = create_relation()
        create_patches(2, project=self.project, related=relation_b)

        patch_a = relation_a.patches.first()
        patch_b = relation_b.patches.first()

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=patch_a.pk), {'related': [patch_b.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

        resp = self.client.patch(
            self.api_url(item=patch_b.pk), {'related': [patch_a.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_cross_project_different_maintainers(self):
        patch_a = create_patch(project=self.project)

        project_b = create_project()
        patch_b = create_patch(project=project_b)

        # maintainer a, patch in own project
        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=patch_a.pk), {'related': [patch_b.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # maintainer a, patch in project b
        resp = self.client.patch(
            self.api_url(item=patch_b.pk), {'related': [patch_a.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_project_relation_super_maintainer(self):
        patch_a = create_patch(project=self.project)

        project_b = create_project()
        patch_b = create_patch(project=project_b)

        project_b.maintainer_project.add(self.maintainer.profile)
        project_b.save()

        self.client.force_authenticate(user=self.maintainer)
        resp = self.client.patch(
            self.api_url(item=patch_a.pk), {'related': [patch_b.pk]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Patch.objects.get(id=patch_a.id).related,
            Patch.objects.get(id=patch_b.id).related,
        )
