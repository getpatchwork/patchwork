# Patchwork - automated patch tracking system
# Copyright (C) 2024 Collabora
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from patchwork.models import Note
from patchwork.tests.api import utils
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_note
from patchwork.tests.utils import create_user
from patchwork.tests.utils import create_superuser


@override_settings(ENABLE_REST_API=True)
class TestPatchNotes(utils.APITestCase):
    def setUp(self):
        super().setUp()
        self.project = create_project()
        self.superuser = create_superuser()
        self.user = create_maintainer(self.project)
        self.patch = create_patch(project=self.project)

    def check_for_expected(self, instance, response_data):
        self.assertEqual(instance.id, response_data['id'])
        self.assertEqual(instance.patch.id, response_data['patch']['id'])
        self.assertEqual(
            instance.submitter.id, response_data['submitter']['id']
        )

    def test_create_note(self):
        start_num = Note.objects.count()
        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        data = {'content': 'New note'}
        self.client.authenticate(user=self.user)
        resp = self.client.post(url, data=data)
        end_num = Note.objects.count()

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(start_num + 1, end_num)

    def test_create_public_note(self):
        start_num = Note.objects.count()
        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        data = {
            'content': 'New note',
            'maintainer_only': False,
        }
        self.client.authenticate(user=self.user)
        resp = self.client.post(url, data=data)
        end_num = Note.objects.count()

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(start_num + 1, end_num)

    def test_get_note_as_super_user(self):
        """Retrieve patch note with an superuser."""
        note = create_note(patch=self.patch)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        self.client.authenticate(user=self.superuser)
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)

    def test_get_note_as_anon_user(self):
        """Retrieve patch note with an anonymous user."""
        note = create_note()

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_get_public_note_as_anon_user(self):
        """Retrieve public patch note with an anon user."""
        note = create_note(patch=self.patch, maintainer_only=False)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)

    def test_get_note_as_maintainer(self):
        """Retrieve patch note with an user that is a maintainer."""
        note = create_note(patch=self.patch, submitter=self.user)

        self.client.authenticate(user=self.user)
        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)

    def test_get_note_as_non_maintainer(self):
        """Retrieve patch note with an user that is not a maintainer."""
        note = create_note()

        self.client.authenticate(user=self.user)
        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_get_note_public(self):
        """Retrieve public patch note with an user that is not a maintainer."""
        person = create_person(user=self.user)
        note = create_note(patch=self.patch, maintainer_only=False)

        self.client.authenticate(user=person.user)
        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)

    def test_get_public_note_list_as_anon_user(self):
        """Retrieve public patch note without authentication."""
        note = create_note(patch=self.patch, maintainer_only=False)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)

    def test_get_note_list_as_super_user(self):
        """Retrieve notes from a patch note without an user."""
        create_note(patch=self.patch, submitter=self.user)
        create_note(
            patch=self.patch, submitter=self.user, maintainer_only=False
        )

        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        self.client.authenticate(user=self.superuser)
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(len(resp.data), 2)

    def test_get_note_list_as_anon_user(self):
        """Retrieve notes from a patch note without an user."""
        create_note(patch=self.patch, submitter=self.user)
        public_note = create_note(
            patch=self.patch, submitter=self.user, maintainer_only=False
        )

        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(len(resp.data), 1)
        self.check_for_expected(public_note, resp.data[0])

    def test_get_note_list_as_maintainer(self):
        """Retrieve notes from a patch note with an user that is a maintainer."""
        create_note(patch=self.patch, submitter=self.user)
        create_note(
            patch=self.patch, submitter=self.user, maintainer_only=False
        )

        self.client.authenticate(user=self.user)
        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(len(resp.data), 2)

    def test_get_note_list_as_non_maintainer(self):
        """Retrieve notes from a patch note with an user that is not a maintainer."""
        create_note(patch=self.patch, submitter=self.user)
        public_note = create_note(
            patch=self.patch, submitter=self.user, maintainer_only=False
        )
        not_maintainer = create_user()

        self.client.authenticate(user=not_maintainer)
        url = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        resp = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], public_note.id)

    def test_edit_note_as_maintainer(self):
        """Edit patch note with an user that is a maintainer."""
        note = create_note(patch=self.patch, submitter=self.user)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        data = {'content': 'New content'}
        self.client.authenticate(user=self.user)
        resp = self.client.patch(url, data=data)

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.check_for_expected(note, resp.data)
        self.assertNotEqual(note.content, resp.data['content'])
        self.assertNotEqual(note.updated_at, resp.data['updated_at'])

    def test_edit_note_as_non_maintainer(self):
        """Edit patch note with an user that is not a maintainer."""
        note = create_note()

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        data = {'content': 'New content'}
        self.client.authenticate(user=self.user)
        resp = self.client.patch(url, data=data)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_edit_note_public_as_non_maintainer(self):
        """
        Edit public patch note with an user that is not a maintainer.
        """
        note = create_note(patch=self.patch, maintainer_only=False)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        data = {'content': 'New content'}
        self.client.authenticate(user=create_user())
        resp = self.client.patch(url, data=data)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_delete_note_as_maintainer(self):
        """Delete patch note with an user that is a maintainer."""
        note = create_note(patch=self.patch, submitter=self.user)
        start_num = Note.objects.count()

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )

        self.client.authenticate(user=self.user)
        resp = self.client.delete(url)
        end_num = Note.objects.count()

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(start_num - 1, end_num)

    def test_delete_note_as_non_maintainer(self):
        """Delete patch note with an user that is not a maintainer."""
        note = create_note()

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )

        self.client.authenticate(user=self.user)
        resp = self.client.delete(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_delete_note_public(self):
        """
        Delete public patch note with an user that is a maintainer with
        an user that is not a maintainer.
        """
        person = create_person()
        note = create_note(patch=self.patch, maintainer_only=False)

        url = reverse(
            'api-patch-note-detail',
            kwargs={'patch_id': self.patch.id, 'note_id': note.id},
        )
        self.client.authenticate(user=person.user)
        resp = self.client.delete(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_notes_in_patch(self):
        url = reverse('api-patch-detail', kwargs={'pk': self.patch.id})
        self.client.authenticate(user=self.user)
        resp = self.client.get(url)

        correct_path = reverse(
            'api-patch-note-list', kwargs={'patch_id': self.patch.id}
        )
        self.assertEqual(
            resp.data.get('notes'),
            f'http://example.com{correct_path}',
        )
