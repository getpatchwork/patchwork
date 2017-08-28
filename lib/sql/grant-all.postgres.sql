BEGIN;
-- give necessary permissions to the web server. Because the admin is all
-- web-based, these need to be quite permissive
GRANT SELECT, UPDATE, INSERT, DELETE ON
	django_session,
	django_site,
	django_admin_log,
	django_content_type,
	auth_group_permissions,
	auth_user,
	auth_user_groups,
	auth_group,
	auth_user_user_permissions,
	auth_permission,
	authtoken_token,
	patchwork_emailconfirmation,
	patchwork_state,
	patchwork_comment,
	patchwork_person,
	patchwork_userprofile,
	patchwork_userprofile_maintainer_projects,
	patchwork_project,
	patchwork_bundle,
	patchwork_bundlepatch,
	patchwork_submission,
	patchwork_patch,
	patchwork_coverletter,
	patchwork_series,
	patchwork_seriespatch,
	patchwork_seriesreference,
	patchwork_emailoptout,
	patchwork_patchchangenotification,
	patchwork_tag,
	patchwork_patchtag,
	patchwork_check,
	patchwork_delegationrule
TO "www-data";
GRANT SELECT, UPDATE ON
	auth_group_id_seq,
	auth_group_permissions_id_seq,
	auth_permission_id_seq,
	auth_user_groups_id_seq,
	auth_user_id_seq,
	auth_user_user_permissions_id_seq,
	django_admin_log_id_seq,
	django_content_type_id_seq,
	django_site_id_seq,
	patchwork_bundle_id_seq,
	patchwork_bundlepatch_id_seq,
	patchwork_comment_id_seq,
	patchwork_patch_id_seq,
	patchwork_series_id_seq,
	patchwork_seriespatch_id_seq,
	patchwork_seriesreference_id_seq,
	patchwork_person_id_seq,
	patchwork_project_id_seq,
	patchwork_state_id_seq,
	patchwork_emailconfirmation_id_seq,
	patchwork_userprofile_id_seq,
	patchwork_userprofile_maintainer_projects_id_seq,
	patchwork_tag_id_seq,
	patchwork_patchtag_id_seq,
	patchwork_check_id_seq,
	patchwork_delegationrule_id_seq
TO "www-data";

-- allow the mail user (in this case, 'nobody') to add submissions (patches,
-- cover letters) and series
GRANT INSERT, SELECT ON
	patchwork_submission,
	patchwork_coverletter,
	patchwork_seriespatch,
	patchwork_seriesreference,
	patchwork_comment,
	patchwork_event
TO "nobody";
GRANT INSERT, SELECT, UPDATE, DELETE ON
	patchwork_patchtag,
	patchwork_patch,
	patchwork_series,
	patchwork_person
TO "nobody";
GRANT SELECT ON
	patchwork_project,
	patchwork_state,
	patchwork_tag,
	patchwork_delegationrule
TO "nobody";
GRANT UPDATE, SELECT ON
	patchwork_patch_id_seq,
	patchwork_series_id_seq,
	patchwork_seriespatch_id_seq,
	patchwork_seriesreference_id_seq,
	patchwork_person_id_seq,
	patchwork_comment_id_seq,
	patchwork_patchtag_id_seq,
	patchwork_event_id_seq
TO "nobody";

COMMIT;

