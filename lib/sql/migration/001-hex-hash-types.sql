BEGIN;
ALTER TABLE patchwork_patch ALTER COLUMN hash DROP NOT NULL;
UPDATE patchwork_patch SET hash = NULL;
COMMIT;
BEGIN;
ALTER TABLE patchwork_patch ALTER COLUMN hash TYPE CHAR(40);
CREATE INDEX "patchwork_patch_hash" ON "patchwork_patch" ("hash");
COMMIT;
