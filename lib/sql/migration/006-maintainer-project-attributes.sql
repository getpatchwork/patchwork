BEGIN;

CREATE TABLE "patchwork_projectmaintainer" (                                    
    "id" serial NOT NULL PRIMARY KEY,
    "project_id" integer NOT NULL
        REFERENCES "patchwork_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL
        REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "master" boolean NOT NULL
);

INSERT INTO patchwork_projectmaintainer
    (project_id, user_id, master)
    SELECT project_id, patchwork_userprofile.user_id, False
        FROM patchwork_userprofile_maintainer_projects
        INNER JOIN patchwork_userprofile
            ON patchwork_userprofile.id =
                patchwork_userprofile_maintainer_projects.userprofile_id;

--DROP TABLE patchwork_userprofile_maintainer_projects;

COMMIT;
