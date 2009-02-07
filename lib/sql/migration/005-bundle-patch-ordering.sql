BEGIN;
ALTER TABLE patchwork_bundle_patches RENAME TO patchwork_bundlepatch;
CREATE SEQUENCE bundlepatch_tmp_seq;

ALTER TABLE patchwork_bundlepatch
	ADD COLUMN "order" INTEGER NOT NULL
		DEFAULT nextval('bundlepatch_tmp_seq');
ALTER TABLE patchwork_bundlepatch ALTER COLUMN "order" DROP DEFAULT;
DROP SEQUENCE bundlepatch_tmp_seq;
ALTER TABLE patchwork_bundlepatch ADD UNIQUE("bundle_id", "order");
UPDATE patchwork_bundlepatch SET "order" = 1 + "order" -
	(SELECT min("order") FROM patchwork_bundlepatch AS p2
		WHERE p2.bundle_id = patchwork_bundlepatch.bundle_id);
COMMIT;
