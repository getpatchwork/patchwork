#!/bin/bash
set -euo pipefail

# functions

test_db_connection() {
    mysqladmin -h $PW_TEST_DB_HOST -u patchwork --password=password ping > /dev/null 2> /dev/null
}

reset_data() {
    mysql -u$db_user -p$db_pass -h $PW_TEST_DB_HOST << EOF
DROP DATABASE IF EXISTS patchwork;
CREATE DATABASE patchwork CHARACTER SET utf8;
GRANT ALL ON patchwork.* TO 'patchwork' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON test_patchwork.* TO 'patchwork'@'%';
FLUSH PRIVILEGES;
EOF

    # load initial data
    python3 $PROJECT_HOME/manage.py migrate #> /dev/null
    python3 $PROJECT_HOME/manage.py loaddata default_tags #> /dev/null
    python3 $PROJECT_HOME/manage.py loaddata default_states #> /dev/null
    python3 $PROJECT_HOME/manage.py loaddata default_projects #> /dev/null
}

# the script begins!

# check if patchwork is mounted. Checking if we exist is a
# very good start!
if [ ! -f ~patchwork/patchwork/tools/docker/entrypoint.sh ]; then
    echo "The patchwork directory doesn't seem to be mounted!"
    echo "Are you using docker-compose?"
    echo "If so, you may need to create an SELinux rule. Refer to the"
    echo "development installation documentation for more information."
    echo "If not, you need -v PATH_TO_PATCHWORK:/home/patchwork/patchwork"
    exit 1
fi

# check if we need to rebuild because requirements changed
for x in /tmp/requirements-*.txt; do
    if ! cmp $x ~/patchwork/$(basename $x); then
        echo "A requirements file has changed."
        echo "Please rebuild the patchwork image:"
        echo "    docker-compose build web"
        exit 1
    fi
done

# check if mysql is connected
if ! test_db_connection; then
    echo "MySQL seems not to be connected, or the patchwork user is broken"
    echo "MySQL may still be starting. Waiting 5 seconds."
    sleep 5
    if ! test_db_connection; then
        echo "Still cannot connect to MySQL."
        echo "Maybe you are starting the db for the first time. Waiting up to 60 seconds."
        for i in {0..9}; do
            sleep 5
            if test_db_connection; then
                break
            fi
        done
        if ! test_db_connection; then
            echo "Still cannot connect to MySQL. Giving up."
            echo "Are you using docker-compose? If not, have you set up the link correctly?"
            exit 1
        fi
    fi
fi

# rebuild mysql db
# do this on --reset or if the db doesn't exist
if [[ "$1" == "--reset" ]]; then
    shift
    reset_data
elif ! ( echo ';' | mysql -h db -u patchwork -ppassword patchwork 2> /dev/null ); then
    reset_data
fi

if [ $# -eq 0 ]; then
    # we probably ran with --reset and nothing else
    # just exit cleanly
    exit 0
elif [ "$1" == "--shell" ]; then
    exec bash
elif [ "$1" == "--quick-test" ]; then
    export PW_SKIP_BROWSER_TESTS=yes
    python3 manage.py test
elif [ "$1" == "--test" ]; then
    xvfb-run --server-args='-screen 0, 1024x768x16' python3 manage.py test
elif [ "$1" == "--quick-tox" ]; then
    shift
    export PW_SKIP_BROWSER_TESTS=yes
    tox $@
elif [ "$1" == "--tox" ]; then
    shift
    xvfb-run --server-args='-screen 0, 1024x768x16' tox $@
else # run whatever CMD is set to
    $@
fi
