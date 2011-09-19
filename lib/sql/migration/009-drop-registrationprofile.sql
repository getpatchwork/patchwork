BEGIN;

DELETE FROM registration_registrationprofile;

-- unlink users who have contributed

UPDATE patchwork_person SET user_id = NULL
    WHERE user_id IN (SELECT id FROM auth_user WHERE is_active = False)
	    AND id IN (SELECT DISTINCT submitter_id FROM patchwork_comment);

-- remove persons who only have a user linkage

DELETE FROM patchwork_person WHERE user_id IN
    (SELECT id FROM auth_user WHERE is_active = False);

-- delete profiles

DELETE FROM patchwork_userprofile WHERE user_id IN
    (SELECT id FROM auth_user WHERE is_active = False);

-- delete inactive users

DELETE FROM auth_user WHERE is_active = False;

DROP TABLE registration_registrationprofile;

COMMIT;
