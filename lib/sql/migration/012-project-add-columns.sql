BEGIN;
ALTER TABLE patchwork_project ADD COLUMN web_url varchar(2000);
ALTER TABLE patchwork_project ADD COLUMN scm_url varchar(2000);
ALTER TABLE patchwork_project ADD COLUMN webscm_url varchar(2000);
COMMIT;
