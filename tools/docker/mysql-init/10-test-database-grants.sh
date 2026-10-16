#!/bin/bash
# Sourced by the MySQL image's entrypoint when initializing a new database.
# Allow Django to create its test database and parallel-test clones.
docker_process_sql <<-EOSQL
    GRANT ALL ON \`test\_${MYSQL_DATABASE}%\`.* TO '${MYSQL_USER}'@'%';
EOSQL
