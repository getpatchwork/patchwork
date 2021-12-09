#!/bin/bash
set -euo pipefail

export DATABASE_HOST=${DATABASE_HOST:-}
export DATABASE_PORT=${DATABASE_PORT:-}
export DATABASE_NAME=${DATABASE_NAME:-patchwork}
export DATABASE_USER=${DATABASE_USER:-patchwork}
export DATABASE_PASSWORD=${DATABASE_PASSWORD:-password}

case "${DATABASE_TYPE:-}" in
postgres)
    export PGPORT=${DATABASE_PORT}
    export PGPASSWORD=${DATABASE_PASSWORD}
    psql_args=( ${DATABASE_HOST:+--host=${DATABASE_HOST}} "--username=${DATABASE_USER}" )
    ;;
*)
    export DATABASE_TYPE=mysql
    mysql_args=( ${DATABASE_HOST:+--host=${DATABASE_HOST}} ${DATABASE_PORT:+--port=${DATABASE_PORT}} "--user=${DATABASE_USER}" "--password=${DATABASE_PASSWORD}" )
    mysql_root_args=( ${DATABASE_HOST:+--host=${DATABASE_HOST}} ${DATABASE_PORT:+--port=${DATABASE_PORT}} "--user=root" "--password=${MYSQL_ROOT_PASSWORD:-}" )
    ;;
esac

# functions

test_db_connection() {
    if [ ${DATABASE_TYPE} = "postgres" ]; then
        echo ';' | psql "${psql_args[@]}" 2> /dev/null > /dev/null
    else
        mysqladmin "${mysql_root_args[@]}" ping > /dev/null 2> /dev/null
    fi
}

test_database() {
    if [ ${DATABASE_TYPE} = "postgres" ]; then
        echo ';' | psql "${psql_args[@]}" "${DATABASE_NAME}" 2> /dev/null
    else
        echo ';' | mysql "${mysql_args[@]}" "${DATABASE_NAME}" 2> /dev/null
    fi
}

reset_data_mysql() {
    mysql "${mysql_root_args[@]}" << EOF
DROP DATABASE IF EXISTS ${DATABASE_NAME};
CREATE DATABASE ${DATABASE_NAME} CHARACTER SET utf8;
GRANT ALL ON ${DATABASE_NAME}.* TO '${DATABASE_USER}' IDENTIFIED BY '${DATABASE_PASSWORD}';
GRANT ALL ON \`test\\_${DATABASE_NAME}%\`.* to '${DATABASE_USER}'@'%';
FLUSH PRIVILEGES;
EOF
}

reset_data_postgres() {
    psql "${psql_args[@]}" <<EOF
DROP DATABASE IF EXISTS ${DATABASE_NAME};
CREATE DATABASE ${DATABASE_NAME} WITH ENCODING = 'UTF8';
EOF
}

reset_data() {
    if [ x${DATABASE_TYPE} = x"postgres" ]; then
        reset_data_postgres
    else
        reset_data_mysql
    fi

    # load initial data
    python manage.py migrate #> /dev/null
    python manage.py loaddata default_tags #> /dev/null
    python manage.py loaddata default_states #> /dev/null
    python manage.py loaddata default_projects #> /dev/null
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
if ! test_db_connection; then
    echo "The database seems not to be connected, or the ${DATABASE_USER} user is broken"
    echo "MySQL/Postgres may still be starting. Waiting 5 seconds."
    sleep 5
    if ! test_db_connection; then
        echo "Still cannot connect to database."
        echo "Maybe you are starting the db for the first time. Waiting up to 60 seconds."
        for i in {0..9}; do
            sleep 5
            if test_db_connection; then
                break
            fi
        done
        if ! test_db_connection; then
            echo "Still cannot connect to database. Giving up."
            echo "Are you using docker-compose? If not, have you set up the link correctly?"
            exit 1
        fi
    fi
fi

# rebuild db
# do this on --reset or if the db doesn't exist
if [[ "$1" == "--reset" ]]; then
    shift
    reset_data
elif ! test_database; then
    reset_data
fi

# TODO(stephenfin): Deprecated the --test, --tox, --quick-test and --quick-tox
# flags in a future release
if [ $# -eq 0 ]; then
    # we probably ran with --reset and nothing else
    # just exit cleanly
    exit 0
elif [ "$1" == "--shell" ]; then
    exec bash
elif [ "$1" == "--test" ] || [ "$1" == "--quick-test" ]; then
    shift
    python manage.py test $@
elif [ "$1" == "--tox" ] || [ "$1" == "--quick-tox" ]; then
    shift
    tox $@
else # run whatever CMD is set to
    $@
fi
