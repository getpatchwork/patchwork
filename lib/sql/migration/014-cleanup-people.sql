BEGIN;
DELETE FROM patchwork_person WHERE id NOT IN (
	SELECT submitter_id FROM patchwork_patch
	UNION
	SELECT submitter_id FROM patchwork_comment)
    AND user_id IS NULL;
COMMIT;
