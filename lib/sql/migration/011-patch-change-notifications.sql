BEGIN;
CREATE TABLE "patchwork_patchchangenotification" (
    "patch_id" integer NOT NULL PRIMARY KEY REFERENCES "patchwork_patch" ("id") DEFERRABLE INITIALLY DEFERRED,
    "last_modified" timestamp with time zone NOT NULL,
    "orig_state_id" integer NOT NULL REFERENCES "patchwork_state" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "patchwork_project" ADD COLUMN
    "send_notifications" boolean NOT NULL DEFAULT False;
ALTER TABLE "patchwork_project" ALTER COLUMN
    "send_notifications" DROP DEFAULT;
COMMIT;
