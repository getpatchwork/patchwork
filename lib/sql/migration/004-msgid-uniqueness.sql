BEGIN;
ALTER TABLE patchwork_patch DROP CONSTRAINT "patchwork_patch_msgid_key";
ALTER TABLE patchwork_comment DROP CONSTRAINT "patchwork_comment_msgid_key";

ALTER TABLE patchwork_patch ADD UNIQUE ("msgid", "project_id");
ALTER TABLE patchwork_comment ADD UNIQUE ("msgid", "patch_id");
COMMIT;
