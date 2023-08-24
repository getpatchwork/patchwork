#!/usr/bin/env bash
#
# Backup a MySQL database

set -e
set -o pipefail

while getopts "h?" opt; do
    case "$opt" in
        h|\?)
            echo "Restore the 'patchwork_backup' database backup to 'patchwork'"
            echo ""
            echo "Only MySQL is currently supported."
            exit 0
            ;;
    esac
done

echo "Checking if 'patchwork' database exists"
if [[ ! $(sudo mysql -e "SHOW DATABASES LIKE 'patchwork'") ]]; then
    echo "There is no 'patchwork' database"
    exit 1
fi

echo "Checking if 'patchwork_backup' database exists"
if [[ ! $(sudo mysql -e "SHOW DATABASES LIKE 'patchwork_backup'") ]]; then
    echo "There is no 'patchwork_backup' database"
    exit 1
fi

read -p "Do you want to proceed? (y/n) " yn
case $yn in
    y)
        ;;
    *)
        exit 0;;
esac

echo "Wiping 'patchwork' database"
sudo mysql -e "DROP DATABASE IF EXISTS patchwork; CREATE DATABASE patchwork;"

echo "Restoring data..."
sudo mysqldump patchwork_backup | sudo mysql patchwork
