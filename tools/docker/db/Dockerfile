FROM mysql:5.7

ENV MYSQL_ROOT_PASSWORD password
ENV MYSQL_USER patchwork
ENV MYSQL_PASSWORD password

# We don't want to use the MYSQL_DATABASE env here because
# we want to be able to create the database with UTF-8 explictly.
# We also can't load in the data because it's in XML, yay.

