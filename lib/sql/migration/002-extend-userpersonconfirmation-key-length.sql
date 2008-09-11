BEGIN;
ALTER TABLE patchwork_userpersonconfirmation
        ALTER COLUMN key TYPE char(40);
COMMIT;
