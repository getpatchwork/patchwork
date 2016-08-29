#!/bin/bash

# Script to set up Patchwork on a Vagrant-powered Ubuntu Trusty host

echo -e "\n--- Configuring environment ---\n"

PROJECT_NAME=patchwork
PROJECT_HOME=/vagrant
WORKON_HOME=$PROJECT_HOME/.virtualenvs

db_user=root
db_pass=password

export DJANGO_SETTINGS_MODULE=patchwork.settings.dev
export DEBIAN_FRONTEND=noninteractive

echo "mysql-server mysql-server/root_password password $db_pass" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password $db_pass" | debconf-set-selections

echo -e "\n--- Updating packages list ---\n"

apt-get update -qq

echo -e "\n--- Installing system packages ---\n"

apt-get install -y python python3-dev python3-pip mysql-server \
    libmysqlclient-dev curl > /dev/null

echo -e "\n--- Installing Python dependencies ---\n"

pip3 -q install virtualenv tox
pip3 -q install -r $PROJECT_HOME/requirements-dev.txt

echo -e "\n--- Configuring database ---\n"

mysql -u$db_user -p$db_pass << EOF
DROP DATABASE IF EXISTS patchwork;
CREATE DATABASE patchwork CHARACTER SET utf8;
GRANT ALL ON patchwork.* TO 'patchwork'@'localhost' IDENTIFIED BY 'password';
EOF

chmod a+x $PROJECT_HOME/manage.py

echo -e "\n--- Loading initial data ---\n"

sudo -E -u vagrant python3 $PROJECT_HOME/manage.py migrate > /dev/null
sudo -E -u vagrant python3 $PROJECT_HOME/manage.py loaddata \
    default_tags > /dev/null
sudo -E -u vagrant python3 $PROJECT_HOME/manage.py loaddata \
    default_states > /dev/null
sudo -E -u vagrant python3 $PROJECT_HOME/manage.py loaddata \
    default_projects > /dev/null

echo -e "\n--- Configuring environment ---\n"

cat >> /home/vagrant/.bashrc << EOF
export DJANGO_SETTINGS_MODULE='patchwork.settings.dev'

alias runserver='python3 /vagrant/manage.py runserver 0.0.0.0:8000'
alias createsu='python3 /vagrant/manage.py createsuperuser'
cd /vagrant
EOF

echo "Done."
echo "You may now log in:"
echo "    $ vagrant ssh"
echo "Once logged in, start the server using the 'runserver' alias:"
echo "    $ runserver"
echo "You may wish to create a superuser for use with the admin console:"
echo "    $ createsuperuser"
echo "For information on the above, and some examples on loading sample date,"
echo "please refer to the documentation found in the 'doc' folder."
echo "Alternatively, check out the docs online:"
echo "    https://patchwork.readthedocs.io/en/latest/development/"
echo "Happy patchworking."
