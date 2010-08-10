BEGIN;
ALTER TABLE "patchwork_comment" ADD COLUMN "parent_id" integer NULL;
ALTER TABLE "patchwork_comment" ADD CONSTRAINT parent_id_refs_id_7b721867
        FOREIGN KEY ("parent_id")
        REFERENCES "patchwork_comment" ("id")
        DEFERRABLE INITIALLY DEFERRED;
COMMIT;
