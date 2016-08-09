FROM ubuntu

ARG UID=1000

ENV PROJECT_HOME /home/patchwork/patchwork

ENV db_user root
ENV db_pass password

ENV DJANGO_SETTINGS_MODULE patchwork.settings.dev
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

# System
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    python-dev python-pip python-setuptools python-wheel \
    python3-dev python3-pip python3-setuptools python3-wheel \
    libmysqlclient-dev mysql-client curl unzip xvfb chromium-chromedriver \
    chromium-browser build-essential && \
    ln -s /usr/lib/chromium-browser/chromedriver /usr/bin/

# User
RUN useradd --uid=$UID --create-home patchwork

# Python requirements.
# If you update requirements, you should rebuild the container.
# entrypoint.sh will prompt you to do this.
COPY requirements-*.txt /tmp/
RUN pip3  install virtualenv tox && \
    pip3  install -r /tmp/requirements-dev.txt
# we deliberately leave the requirements files in tmp so we can
# ping the user in entrypoint.sh if the change them!

COPY docker/bashrc /tmp/bashrc

# we put the code in ~/patchwork rather than ~ so that we
# can put in these bashrc snippets without dirtying the
# working directory
RUN cat /tmp/bashrc >> /home/patchwork/.bashrc

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
USER patchwork
WORKDIR /home/patchwork/patchwork
