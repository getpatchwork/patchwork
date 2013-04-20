BEGIN;
UPDATE patchwork_bundle
	SET name = replace(name, '/', '-')
	WHERE name like '%/%';
COMMIT;

