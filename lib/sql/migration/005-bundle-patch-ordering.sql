BEGIN;
CREATE TABLE "patchwork_bundlepatch" (                                          
    "id" SERIAL NOT NULL PRIMARY KEY,
    "patch_id" INTEGER NOT NULL
        REFERENCES "patchwork_patch" ("id") DEFERRABLE INITIALLY DEFERRED,
    "bundle_id" INTEGER NOT NULL
        REFERENCES "patchwork_bundle" ("id") DEFERRABLE INITIALLY DEFERRED,
    "order" SERIAL NOT NULL,
    UNIQUE ("bundle_id", "patch_id")
);

-- we 'INSERT INTO ... SELECT' (rather than renaming and adding the order
-- column) here so that we can order by date
INSERT INTO patchwork_bundlepatch (id, patch_id, bundle_id)
    SELECT patchwork_bundle_patches.id, patch_id, bundle_id
        FROM patchwork_bundle_patches
        INNER JOIN patchwork_patch
            ON patchwork_patch.id = patchwork_bundle_patches.patch_id
        ORDER BY bundle_id, patchwork_patch.date;
COMMIT;

BEGIN;
ALTER TABLE patchwork_bundlepatch
    ALTER COLUMN "order" TYPE INTEGER;

-- normalise ordering: order should start with 1 in each bundle
UPDATE patchwork_bundlepatch SET "order" = 1 + "order" -
	(SELECT min("order") FROM patchwork_bundlepatch AS p2
		WHERE p2.bundle_id = patchwork_bundlepatch.bundle_id);

SELECT * FROM patchwork_bundlepatch;
COMMIT;
