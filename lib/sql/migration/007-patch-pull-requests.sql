BEGIN;
ALTER TABLE patchwork_patch ADD column pull_url varchar(255);
ALTER TABLE patchwork_patch ALTER COLUMN content DROP NOT NULL;
ALTER TABLE patchwork_patch ADD CONSTRAINT has_content_or_url
	CHECK (pull_url IS NOT NULL OR content IS NOT NULL);
COMMIT;
