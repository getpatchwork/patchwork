BEGIN;
-- give necessary permissions to the web server. Because the admin is all
-- web-based, these need to be quite permissive
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_group TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_group_permissions TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_permission TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user_groups TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user_user_permissions TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON authtoken_token TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_admin_log TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_content_type TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_session TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_site TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_bundle TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_bundlepatch TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_check TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_comment TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_coverletter TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_delegationrule TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_emailconfirmation TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_emailoptout TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_event TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_patch TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_patchchangenotification TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_patchrelation TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_patchtag TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_person TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_project TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_series TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_seriesreference TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_state TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_submission TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_tag TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_userprofile TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_userprofile_maintainer_projects TO 'www-data'@localhost;

-- allow the mail user (in this case, 'nobody') to add submissions (patches,
-- cover letters) and series
GRANT INSERT, SELECT ON patchwork_comment TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_coverletter TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_event TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_patch TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_person TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_series TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_seriesreference TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_submission TO 'nobody'@localhost;
GRANT INSERT, SELECT, UPDATE, DELETE ON patchwork_patchtag TO 'nobody'@localhost;
GRANT SELECT ON auth_user TO 'nobody'@localhost;
GRANT SELECT ON patchwork_delegationrule TO 'nobody'@localhost;
GRANT SELECT ON	patchwork_project TO 'nobody'@localhost;
GRANT SELECT ON patchwork_state TO 'nobody'@localhost;
GRANT SELECT ON patchwork_tag TO 'nobody'@localhost;

COMMIT;
