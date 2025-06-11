# Patchwork - automated patch tracking system
# Copyright (C) 2025 ProFUSION
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from patchwork.models import PatchComment
from patchwork.models import CoverComment
from patchwork.tests.api import utils
from patchwork.tests.utils import create_cover
from patchwork.tests.utils import create_cover_comment
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_patch_comment
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_user


@override_settings(ENABLE_REST_API=True)
class TestPatchMaintainerNotes(utils.APITestCase):
    @staticmethod
    def api_url(patch, version=None, item=None):
        kwargs = {'patch_id': patch.id}
        if version:
            kwargs['version'] = version
        if item is None:
            return reverse('api-patch-comment-list', kwargs=kwargs)
        kwargs['comment_id'] = item.id
        return reverse('api-patch-comment-detail', kwargs=kwargs)

    def setUp(self):
        super(TestPatchMaintainerNotes, self).setUp()
        self.project = create_project()
        self.maintainer = create_maintainer(self.project)
        self.maintainer_person = self.maintainer.person_set.first()
        self.patch = create_patch(project=self.project)

        # Another maintainer for testing editing other's notes
        self.other_maintainer = create_maintainer(
            self.project,
            username='other_maintainer',
            email='other@example.com',
        )
        self.other_person = self.other_maintainer.person_set.first()

    def assertMaintainerNote(self, note_obj, note_json):
        """Assert a maintainer note is correctly serialized."""
        self.assertEqual(note_obj.id, note_json['id'])
        self.assertEqual(note_obj.submitter.id, note_json['submitter']['id'])
        self.assertEqual('', note_obj.msgid)
        self.assertIn(note_obj.content, note_json['content'])

    def test_create_maintainer_note(self):
        """Test creating a maintainer note for a patch."""
        self.client.authenticate(user=self.maintainer)

        data = {'content': 'This is a maintainer note', 'addressed': None}
        resp = self.client.post(self.api_url(self.patch), data)

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, PatchComment.objects.filter(msgid='').count())

        note = PatchComment.objects.get(msgid='')
        self.assertEqual(data['content'], note.content)
        self.assertEqual(self.maintainer_person, note.submitter)
        self.assertMaintainerNote(note, resp.data)

    def test_create_note_non_maintainer(self):
        """Test that a non-maintainer cannot create a maintainer note."""
        user = create_user()
        self.client.authenticate(user=user)

        resp = self.client.post(
            self.api_url(self.patch), {'content': 'This should fail'}
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertEqual(0, PatchComment.objects.filter(msgid='').count())

    def test_duplicate_maintainer_note(self):
        """Test that we can't create duplicate maintainer notes for a patch."""
        self.client.authenticate(user=self.maintainer)

        resp = self.client.post(
            self.api_url(self.patch), {'content': 'First maintainer note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Second maintainer note - should fail'},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn('Maintaner note already exists', str(resp.data))

    def test_update_own_maintainer_note(self):
        """Test updating a maintainer note as the original creator."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Original content'}
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        updated_content = 'Updated content'
        resp = self.client.patch(
            self.api_url(self.patch, item=note), {'content': updated_content}
        )

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        note.refresh_from_db()
        self.assertEqual(updated_content, note.content)
        self.assertEqual(updated_content, resp.data['content'])

    def test_update_others_maintainer_note(self):
        """Test that a maintainer can update another maintainer's note."""
        # First maintainer creates a note
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Original content from first maintainer'},
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        # Second maintainer updates it
        self.client.authenticate(user=self.other_maintainer)
        updated_content = 'Updated by second maintainer'
        resp = self.client.patch(
            self.api_url(self.patch, item=note), {'content': updated_content}
        )

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        note.refresh_from_db()
        self.assertEqual(updated_content, note.content)
        self.assertEqual(updated_content, resp.data['content'])

        # Submitter should not change
        self.assertEqual(
            self.maintainer_person.id, resp.data['submitter']['id']
        )
        self.assertEqual(self.maintainer_person, note.submitter)

    def test_update_note_non_maintainer(self):
        """Test that a non-maintainer cannot update a maintainer note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Original content'}
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.patch(
            self.api_url(self.patch, item=note),
            {'content': 'This should fail'},
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        note.refresh_from_db()
        self.assertEqual('Original content', note.content)

    def test_list_includes_maintainer_notes_with_filter(self):
        """Test that maintainer notes are included when using the type filter."""
        create_patch_comment(patch=self.patch)

        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Maintainer note'}
        )
        note_id = resp.data['id']

        # Get list of comments with type=notes filter
        resp = self.client.get(self.api_url(self.patch), {'type': 'notes'})

        # Should include only the note
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])
        self.assertEqual('Maintainer note', resp.data[0]['content'])

    def test_delete_maintainer_note(self):
        """Test deleting a maintainer note as a maintainer."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Note to be deleted'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        resp = self.client.delete(self.api_url(self.patch, item=note))
        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(0, PatchComment.objects.filter(id=note_id).count())

    def test_delete_maintainer_note_by_other_maintainer(self):
        """Test that another maintainer can delete a maintainer note."""
        # First maintainer creates a note
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Note created by first maintainer'},
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        # Second maintainer deletes it
        self.client.authenticate(user=self.other_maintainer)
        resp = self.client.delete(self.api_url(self.patch, item=note))

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(0, PatchComment.objects.filter(id=note_id).count())

    def test_delete_maintainer_note_by_non_maintainer(self):
        """Test that a non-maintainer cannot delete a maintainer note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Note that should not be deletable'},
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.delete(self.api_url(self.patch, item=note))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertTrue(PatchComment.objects.filter(id=note_id).exists())

    def test_delete_regular_comment_fails(self):
        """Test that regular comments cannot be deleted via the API."""
        comment = create_patch_comment(
            patch=self.patch, content='Regular comment'
        )

        self.client.authenticate(user=self.maintainer)
        resp = self.client.delete(self.api_url(self.patch, item=comment))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertIn('Only maintainer notes can be deleted', str(resp.data))

    def test_filter_by_type_notes(self):
        """Test filtering comments to show only maintainer notes."""
        create_patch_comment(patch=self.patch, content='Regular comment')

        self.client.authenticate(user=self.maintainer)
        note_resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Maintainer note for filtering'},
        )
        note_id = note_resp.data['id']

        # Filter to only show notes
        resp = self.client.get(
            self.api_url(self.patch),
            {'type': 'notes'},
        )

        # Should include only the note, not the regular comment
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])
        self.assertEqual(
            'Maintainer note for filtering', resp.data[0]['content']
        )
        self.assertEqual('', resp.data[0]['msgid'])

    def test_filter_by_type_comments(self):
        """Test filtering to show only regular comments (exclude notes)."""
        regular_comment = create_patch_comment(
            patch=self.patch, content='Regular comment for filtering'
        )

        self.client.authenticate(user=self.maintainer)
        self.client.post(
            self.api_url(self.patch),
            {'content': 'Maintainer note'},
        )

        # Filter to only show regular comments
        resp = self.client.get(self.api_url(self.patch), {'type': 'comments'})

        # Should include only the regular comment, not the note
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(regular_comment.id, resp.data[0]['id'])
        self.assertEqual(
            'Regular comment for filtering', resp.data[0]['content']
        )
        self.assertNotEqual('', resp.data[0]['msgid'])

    def test_authentication_required_for_delete(self):
        """Test that authentication is required for DELETE operations."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Note to be deleted'}
        )
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        self.client.authenticate(user=None)
        resp = self.client.delete(self.api_url(self.patch, item=note))
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertIn('permission_denied', str(resp.data).lower())

    def test_get_list_default_excludes_notes(self):
        """Test that the default GET behavior excludes maintainer notes."""
        regular_comment = create_patch_comment(
            patch=self.patch, content='Regular comment'
        )

        self.client.authenticate(user=self.maintainer)
        self.client.post(
            self.api_url(self.patch),
            {'content': 'Hidden maintainer note'},
        )

        self.client.authenticate(user=None)  # No auth needed for GET
        resp = self.client.get(self.api_url(self.patch))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(regular_comment.id, resp.data[0]['id'])

    def test_non_maintainer_can_access_filtered_notes(self):
        """Test that non-maintainers can access notes with the filter."""
        self.client.authenticate(user=self.maintainer)
        note_resp = self.client.post(
            self.api_url(self.patch), {'content': 'Maintainer note'}
        )
        note_id = note_resp.data['id']

        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.get(self.api_url(self.patch), {'type': 'notes'})

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])

    def test_no_modification_of_msgid_field(self):
        """Test that msgid cannot be explicitly set or modified."""
        self.client.authenticate(user=self.maintainer)

        # Try to create a maintainer note with a non-empty msgid
        resp = self.client.post(
            self.api_url(self.patch),
            {'content': 'Note with msgid', 'msgid': '<test@example.com>'},
        )

        # Should succeed, but msgid should be empty (MessageID ignored in request)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual('', resp.data['msgid'])
        note = PatchComment.objects.get(id=resp.data['id'])
        self.assertEqual('', note.msgid)

    def test_maintainer_serializer_used(self):
        """Test that the correct serializer is used based on method/model."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Maintainer note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        note_id = resp.data['id']
        note = PatchComment.objects.get(id=note_id)

        other_user = create_user(username='test_other')
        self.client.authenticate(user=self.maintainer)

        # Try to update submitter field (should be ignored as it's read-only)
        resp = self.client.patch(
            self.api_url(self.patch, item=note),
            {'content': 'Updated note', 'submitter': {'id': other_user.id}},
        )

        # Should succeed but submitter shouldn't change
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual('Updated note', resp.data['content'])
        self.assertEqual(
            self.maintainer_person.id, resp.data['submitter']['id']
        )

    def test_validation_error_has_proper_message(self):
        """Test that validation errors have the correct message format."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.patch), {'content': 'First note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        resp = self.client.post(
            self.api_url(self.patch), {'content': 'Second note - should fail'}
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn('Maintaner note already exists', str(resp.data))
        self.assertIn('patch', str(resp.data).lower())


@override_settings(ENABLE_REST_API=True)
class TestCoverMaintainerNotes(utils.APITestCase):
    @staticmethod
    def api_url(cover, version=None, item=None):
        kwargs = {'cover_id': cover.id}
        if version:
            kwargs['version'] = version
        if item is None:
            return reverse('api-cover-comment-list', kwargs=kwargs)
        kwargs['comment_id'] = item.id
        return reverse('api-cover-comment-detail', kwargs=kwargs)

    def setUp(self):
        super(TestCoverMaintainerNotes, self).setUp()
        self.project = create_project()
        self.maintainer = create_maintainer(self.project)
        self.maintainer_person = self.maintainer.person_set.first()
        self.cover = create_cover(project=self.project)

        # Another maintainer for testing editing other's notes
        self.other_maintainer = create_maintainer(
            self.project,
            username='other_maintainer',
            email='other@example.com',
        )
        self.other_person = self.other_maintainer.person_set.first()

    def assertMaintainerNote(self, note_obj, note_json):
        """Assert a maintainer note is correctly serialized."""
        self.assertEqual(note_obj.id, note_json['id'])
        self.assertEqual(note_obj.submitter.id, note_json['submitter']['id'])
        self.assertEqual('', note_obj.msgid)
        self.assertIn(note_obj.content, note_json['content'])

    def test_create_maintainer_note(self):
        """Test creating a maintainer note for a cover letter."""
        self.client.authenticate(user=self.maintainer)

        data = {'content': 'This is a cover maintainer note'}
        resp = self.client.post(self.api_url(self.cover), data)

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, CoverComment.objects.filter(msgid='').count())

        note = CoverComment.objects.get(msgid='')
        self.assertEqual(data['content'], note.content)
        self.assertEqual(self.maintainer_person, note.submitter)
        self.assertMaintainerNote(note, resp.data)

    def test_create_note_non_maintainer(self):
        """Test that a non-maintainer cannot create a maintainer note."""
        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'This should fail'}
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertEqual(0, CoverComment.objects.filter(msgid='').count())

    def test_duplicate_maintainer_note(self):
        """Test that we can't create duplicate maintainer notes for a cover."""
        self.client.authenticate(user=self.maintainer)

        resp = self.client.post(
            self.api_url(self.cover), {'content': 'First maintainer note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Second maintainer note - should fail'},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn('Maintaner note already exists', str(resp.data))
        self.assertEqual(1, CoverComment.objects.filter(msgid='').count())

    def test_update_own_maintainer_note(self):
        """Test updating a maintainer note as the original creator."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Original content'}
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        updated_content = 'Updated content'
        resp = self.client.patch(
            self.api_url(self.cover, item=note), {'content': updated_content}
        )

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        note.refresh_from_db()
        self.assertEqual(updated_content, note.content)
        self.assertEqual(updated_content, resp.data['content'])

    def test_update_others_maintainer_note(self):
        """Test that a maintainer can update another maintainer's note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Original content from first maintainer'},
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        # Second maintainer updates it
        self.client.authenticate(user=self.other_maintainer)
        updated_content = 'Updated by second maintainer'
        resp = self.client.patch(
            self.api_url(self.cover, item=note), {'content': updated_content}
        )

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        note.refresh_from_db()
        self.assertEqual(updated_content, note.content)
        self.assertEqual(updated_content, resp.data['content'])
        self.assertEqual(
            self.maintainer_person.id, resp.data['submitter']['id']
        )
        self.assertEqual(self.maintainer_person, note.submitter)

    def test_update_note_non_maintainer(self):
        """Test that a non-maintainer cannot update a maintainer note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Original content'}
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        # Try to update as non-maintainer
        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.patch(
            self.api_url(self.cover, item=note),
            {'content': 'This should fail'},
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        note.refresh_from_db()
        self.assertEqual('Original content', note.content)

    def test_list_includes_maintainer_notes_with_filter(self):
        """Test that maintainer notes are included when using the type filter."""
        create_cover_comment(cover=self.cover)

        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Maintainer note'}
        )
        note_id = resp.data['id']

        resp = self.client.get(self.api_url(self.cover), {'type': 'notes'})

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])
        self.assertEqual('Maintainer note', resp.data[0]['content'])

    def test_delete_maintainer_note(self):
        """Test deleting a maintainer note as a maintainer."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Note to be deleted'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        resp = self.client.delete(self.api_url(self.cover, item=note))
        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(0, CoverComment.objects.filter(id=note_id).count())

    def test_delete_maintainer_note_by_other_maintainer(self):
        """Test that another maintainer can delete a maintainer note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Note created by first maintainer'},
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        # Second maintainer deletes it
        self.client.authenticate(user=self.other_maintainer)
        resp = self.client.delete(self.api_url(self.cover, item=note))

        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)
        self.assertEqual(0, CoverComment.objects.filter(id=note_id).count())

    def test_delete_maintainer_note_by_non_maintainer(self):
        """Test that a non-maintainer cannot delete a maintainer note."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Note that should not be deletable'},
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        # Try to delete as non-maintainer
        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.delete(self.api_url(self.cover, item=note))

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertTrue(CoverComment.objects.filter(id=note_id).exists())

    def test_delete_regular_comment_fails(self):
        """Test that regular comments cannot be deleted via the API."""
        comment = create_cover_comment(
            cover=self.cover, content='Regular comment'
        )

        self.client.authenticate(user=self.maintainer)
        resp = self.client.delete(self.api_url(self.cover, item=comment))

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertIn('Only maintainer notes can be deleted', str(resp.data))

    def test_filter_by_type_notes(self):
        """Test filtering comments to show only maintainer notes."""
        create_cover_comment(cover=self.cover, content='Regular comment')

        self.client.authenticate(user=self.maintainer)
        note_resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Maintainer note for filtering'},
        )
        note_id = note_resp.data['id']

        # Filter to only show notes
        resp = self.client.get(self.api_url(self.cover), {'type': 'notes'})

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])
        self.assertEqual(
            'Maintainer note for filtering', resp.data[0]['content']
        )
        self.assertEqual('', resp.data[0]['msgid'])

    def test_filter_by_type_comments(self):
        """Test filtering to show only regular comments (exclude notes)."""

        regular_comment = create_cover_comment(
            cover=self.cover, content='Regular comment for filtering'
        )

        self.client.authenticate(user=self.maintainer)
        self.client.post(
            self.api_url(self.cover),
            {'content': 'Maintainer note'},
        )

        # Filter to only show regular comments
        resp = self.client.get(self.api_url(self.cover), {'type': 'comments'})

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(regular_comment.id, resp.data[0]['id'])
        self.assertEqual(
            'Regular comment for filtering', resp.data[0]['content']
        )
        self.assertNotEqual('', resp.data[0]['msgid'])

    def test_authentication_required_for_delete(self):
        """Test that authentication is required for DELETE operations."""
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Note to be deleted'}
        )
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        self.client.authenticate(user=None)
        resp = self.client.delete(self.api_url(self.cover, item=note))

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        self.assertIn('permission_denied', str(resp.data).lower())

    def test_get_list_default_excludes_notes(self):
        """Test that the default GET behavior excludes maintainer notes."""
        regular_comment = create_cover_comment(
            cover=self.cover, content='Regular comment'
        )

        self.client.authenticate(user=self.maintainer)
        self.client.post(
            self.api_url(self.cover), {'content': 'Hidden maintainer note'}
        )

        self.client.authenticate(user=None)  # No auth needed for GET
        resp = self.client.get(self.api_url(self.cover))

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(regular_comment.id, resp.data[0]['id'])

    def test_non_maintainer_can_access_filtered_notes(self):
        """Test that non-maintainers can access notes with the filter."""
        self.client.authenticate(user=self.maintainer)
        note_resp = self.client.post(
            self.api_url(self.cover), {'content': 'Maintainer note'}
        )
        note_id = note_resp.data['id']

        # Non-maintainer user should still be able to see notes with filter
        user = create_user()
        self.client.authenticate(user=user)
        resp = self.client.get(self.api_url(self.cover), {'type': 'notes'})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(note_id, resp.data[0]['id'])

    def test_no_modification_of_msgid_field(self):
        """Test that msgid cannot be explicitly set or modified."""
        self.client.authenticate(user=self.maintainer)

        # Try to create a maintainer note with a non-empty msgid
        resp = self.client.post(
            self.api_url(self.cover),
            {'content': 'Note with msgid', 'msgid': '<test@example.com>'},
        )

        # Should succeed, but msgid should be empty (MessageID ignored in request)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual('', resp.data['msgid'])

        # Verify in database
        note = CoverComment.objects.get(id=resp.data['id'])
        self.assertEqual('', note.msgid)

    def test_maintainer_serializer_used(self):
        """Test that the correct serializer is used based on method/model."""
        # Create a note first
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Maintainer note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        note_id = resp.data['id']
        note = CoverComment.objects.get(id=note_id)

        # Check that read-only fields are respected - try to change submitter
        other_user = create_user(username='test_other')
        self.client.authenticate(user=self.maintainer)

        # Try to update submitter field (should be ignored as it's read-only)
        resp = self.client.patch(
            self.api_url(self.cover, item=note),
            {'content': 'Updated note', 'submitter': {'id': other_user.id}},
        )

        # Should succeed but submitter shouldn't change
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual('Updated note', resp.data['content'])
        self.assertEqual(
            self.maintainer_person.id, resp.data['submitter']['id']
        )

    def test_validation_error_has_proper_message(self):
        """Test that validation errors have the correct message format."""
        # Create a maintainer note
        self.client.authenticate(user=self.maintainer)
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'First note'}
        )
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        # Try to create another one
        resp = self.client.post(
            self.api_url(self.cover), {'content': 'Second note - should fail'}
        )

        # Should fail with proper error message
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertIn('Maintaner note already exists', str(resp.data))
        self.assertIn(
            'cover', str(resp.data).lower()
        )  # Mentions it's for a cover
