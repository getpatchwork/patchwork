BEGIN;
-- give necessary permissions to the web server. Because the admin is all
-- web-based, these need to be quite permissive
GRANT SELECT, UPDATE, INSERT, DELETE ON
	auth_group,
	auth_group_permissions,
	auth_user,
	auth_user_groups,
	auth_user_user_permissions,
	auth_permission,
	authtoken_token,
	django_admin_log,
	django_content_type,
	django_session,
	django_site,
	patchwork_bundle,
	patchwork_bundlepatch,
	patchwork_check,
	patchwork_comment,
	patchwork_coverletter,
	patchwork_delegationrule,
	patchwork_emailconfirmation,
	patchwork_emailoptout,
	patchwork_event,
	patchwork_patch,
	patchwork_patchchangenotification,
	patchwork_patchrelation,
	patchwork_patchtag,
	patchwork_person,
	patchwork_project,
	patchwork_series,
	patchwork_seriesreference,
	patchwork_state,
	patchwork_submission,
	patchwork_tag,
	patchwork_userprofile,
	patchwork_userprofile_maintainer_projects
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
	patchwork_check_id_seq,
	patchwork_comment_id_seq,
	patchwork_delegationrule_id_seq,
	patchwork_emailconfirmation_id_seq,
	patchwork_event_id_seq,
	patchwork_patch_id_seq,
	patchwork_patchrelation_id_seq,
	patchwork_patchtag_id_seq,
	patchwork_person_id_seq,
	patchwork_project_id_seq,
	patchwork_series_id_seq,
	patchwork_seriesreference_id_seq,
	patchwork_state_id_seq,
	patchwork_tag_id_seq,
	patchwork_userprofile_id_seq,
	patchwork_userprofile_maintainer_projects_id_seq
TO "www-data";

-- allow the mail user (in this case, 'nobody') to add submissions (patches,
-- cover letters) and series
GRANT INSERT, SELECT ON
	patchwork_comment,
	patchwork_coverletter,
	patchwork_event,
	patchwork_seriesreference
TO "nobody";
GRANT INSERT, SELECT, UPDATE ON
	patchwork_submission
TO "nobody";
GRANT INSERT, SELECT, UPDATE, DELETE ON
	patchwork_patch,
	patchwork_patchtag,
	patchwork_person,
	patchwork_series
TO "nobody";
GRANT SELECT ON
	auth_user,
	patchwork_delegationrule,
	patchwork_project,
	patchwork_state,
	patchwork_tag
TO "nobody";
GRANT UPDATE, SELECT ON
	patchwork_comment_id_seq,
	patchwork_event_id_seq,
	patchwork_patch_id_seq,
	patchwork_patchtag_id_seq,
	patchwork_person_id_seq,
	patchwork_series_id_seq,
	patchwork_seriesreference_id_seq
TO "nobody";

COMMIT;
