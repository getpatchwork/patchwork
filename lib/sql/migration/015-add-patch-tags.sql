BEGIN;
ALTER TABLE patchwork_project ADD COLUMN use_tags boolean default true;

CREATE TABLE "patchwork_tag" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "pattern" varchar(50) NOT NULL,
    "abbrev" varchar(2) NOT NULL UNIQUE
);

CREATE TABLE "patchwork_patchtag" (
    "id" serial NOT NULL PRIMARY KEY,
    "patch_id" integer NOT NULL,
    "tag_id" integer NOT NULL REFERENCES "patchwork_tag" ("id"),
    "count" integer NOT NULL,
    UNIQUE ("patch_id", "tag_id")
);

COMMIT;
