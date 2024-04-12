#!/bin/bash
set -euo pipefail

export DATABASE_HOST=${DATABASE_HOST:-}
export DATABASE_PORT=${DATABASE_PORT:-}
export DATABASE_USER=${DATABASE_USER:-patchwork}
export DATABASE_PASSWORD=${DATABASE_PASSWORD:-password}

case "${DATABASE_TYPE:-}" in
postgres)
    export DATABASE_NAME=${DATABASE_NAME:-patchwork}
    export PGPORT=${DATABASE_PORT}
    export PGPASSWORD=${DATABASE_PASSWORD}
    psql_args=( ${DATABASE_HOST:+--host=${DATABASE_HOST}} "--username=${DATABASE_USER}" )
    ;;
sqlite3)
    export DATABASE_NAME=${DATABASE_NAME:-/dev/shm/patchwork.db.sqlite3}
    ;;
*)
    export DATABASE_TYPE=mysql
    export DATABASE_NAME=${DATABASE_NAME:-patchwork}
    mysql_args=( ${DATABASE_HOST:+--host=${DATABASE_HOST}} ${DATABASE_PORT:+--port=${DATABASE_PORT}} "--user=${DATABASE_USER}" "--password=${DATABASE_PASSWORD}" )
    ;;
esac

# functions

test_database() {
    case "${DATABASE_TYPE}" in
    "postgres")
        echo ';' | psql "${psql_args[@]}" "${DATABASE_NAME}" 2> /dev/null ;;
    "mysql")
        echo ';' | mysql "${mysql_args[@]}" "${DATABASE_NAME}" 2> /dev/null ;;
    "sqlite3")
        echo ';' | sqlite3 "${DATABASE_NAME}" > /dev/null 2> /dev/null ;;
    esac
}

# the script begins!

# check if patchwork is mounted. Checking if we exist is a
# very good start!
if [ ! -f ~patchwork/patchwork/tools/docker/entrypoint.sh ]; then
    cat << EOF
The patchwork directory doesn't seem to be mounted!

Are you using docker-compose? If so, you may need to create an SELinux rule.
Refer to the development installation documentation for more information.
If not, you need -v PATH_TO_PATCHWORK:/home/patchwork/patchwork
EOF
    exit 1
fi

set +e

# check if we need to rebuild because requirements changed
for x in /opt/requirements-*.txt; do
    if ! cmp $x ~/patchwork/$(basename $x); then
        cat << EOF
A requirements file has changed.

You may need to rebuild the patchwork image:

    docker-compose build web
EOF
        diff -u $x ~/patchwork/$(basename $x)
    fi
done

set -e

# check if db is connected
if ! test_database; then
    echo "The database seems not to be connected, or the ${DATABASE_USER} user is broken"
    echo "MySQL/Postgres may still be starting. Waiting 5 seconds."
    sleep 5
    if ! test_database; then
        echo "Still cannot connect to database."
        echo "Maybe you are starting the db for the first time. Waiting up to 60 seconds."
        for i in {0..9}; do
            sleep 5
            if test_database; then
                break
            fi
        done
        if ! test_database; then
            echo "Still cannot connect to database. Giving up."
            echo "Are you using docker-compose? If not, have you set up the link correctly?"
            exit 1
        fi
    fi
fi

# load initial data but only if we haven't loaded it before
# HACK: We choose an arbitrary Django migration since we don't want to apply
# Patchwork migrations by default each time since they might be WIP. The
# 'sessions' migrations look unlikely to change very often.
if ! python manage.py migrate sessions --check -v0; then
    python manage.py migrate #> /dev/null
    python manage.py loaddata default_tags #> /dev/null
    python manage.py loaddata default_states #> /dev/null
    python manage.py loaddata default_projects #> /dev/null
fi

cron
exec "$@"
