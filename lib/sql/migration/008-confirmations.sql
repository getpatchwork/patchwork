BEGIN;
ALTER TABLE "patchwork_userpersonconfirmation"
        RENAME TO "patchwork_emailconfirmation";
ALTER SEQUENCE "patchwork_userpersonconfirmation_id_seq"
        RENAME TO "patchwork_emailconfirmation_id_seq";
ALTER TABLE "patchwork_emailconfirmation"
        ALTER COLUMN "user_id" DROP NOT NULL,
        ADD COLUMN "type" varchar(20) NOT NULL DEFAULT 'userperson';
ALTER TABLE "patchwork_emailconfirmation"
        ALTER COLUMN "type" DROP DEFAULT;
COMMIT;
