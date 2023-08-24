#!/usr/bin/env bash
#
# Backup a MySQL database

set -e
set -o pipefail

while getopts "h?" opt; do
    case "$opt" in
        h|\?)
            echo "Backup the 'patchwork' database to 'patchwork_backup'"
            echo ""
            echo "Does not rotate backups. Only MySQL is currently supported."
            exit 0
            ;;
    esac
done

echo "Checking if 'patchwork' database exists"
if [[ ! $(sudo mysql -e "SHOW DATABASES LIKE 'patchwork'") ]]; then
    echo "There is no 'patchwork' database"
    exit 1
fi

read -p "Do you want to proceed? (y/n) " yn
case $yn in
    y)
        ;;
    *)
        exit 0;;
esac

echo "Creating patchwork_backup database"
sudo mysql -e "DROP DATABASE IF EXISTS patchwork_backup; CREATE DATABASE patchwork_backup;"

echo "Backing up data..."
sudo mysqldump patchwork | sudo mysql patchwork_backup
