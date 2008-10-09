BEGIN;
-- give necessary permissions to the web server. Becuase the admin is all
-- web-based, these need to be quite permissive
GRANT SELECT, UPDATE, INSERT, DELETE ON	auth_message TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_session TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_site TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_admin_log TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON django_content_type TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_group_permissions TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user_groups TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_group TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_user_user_permissions TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON auth_permission TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_userpersonconfirmation TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_state TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_comment TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_person TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_userprofile TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_userprofile_maintainer_projects TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_project TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_bundle TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_bundle_patches TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON patchwork_patch TO 'www-data'@localhost;
GRANT SELECT, UPDATE, INSERT, DELETE ON registration_registrationprofile TO 'www-data'@localhost;

-- allow the mail user (in this case, 'nobody') to add patches
GRANT INSERT, SELECT ON patchwork_patch TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_comment TO 'nobody'@localhost;
GRANT INSERT, SELECT ON patchwork_person TO 'nobody'@localhost;
GRANT SELECT ON	patchwork_project TO 'nobody'@localhost;
GRANT SELECT ON patchwork_state TO 'nobody'@localhost;

COMMIT;

