BEGIN;
ALTER TABLE patchwork_bundle_patches RENAME TO patchwork_bundlepatch;
ALTER TABLE patchwork_bundlepatch ADD COLUMN "order" INTEGER NULL;
UPDATE patchwork_bundlepatch SET "order" =
    (SELECT COALESCE(max("order"), 0) + 1 FROM patchwork_bundlepatch AS p2
        WHERE p2.bundle_id = patchwork_bundlepatch.bundle_id);
ALTER TABLE patchwork_bundlepatch ALTER COLUMN "order" SET NOT NULL;
ALTER TABLE patchwork_bundlepatch ADD UNIQUE("bundle_id", "order");
COMMIT;
