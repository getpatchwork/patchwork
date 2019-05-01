FROM ubuntu:18.04

ARG UID
ARG TZ="Australia/Canberra"

RUN echo $UID
RUN [ -n "$UID" ] || { echo "You must define UID in .env" 1>&2; exit 1; }

ENV PROJECT_HOME /home/patchwork/patchwork

ENV db_user root
ENV db_pass password

ENV DJANGO_SETTINGS_MODULE patchwork.settings.dev
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1


# System
# trusty and findutils is for python3.4; xenial is for python3.5
# TODO(stephenfin): Are curl, unzip required?
COPY tools/docker/*.list /etc/apt/sources.list.d/

RUN cd /etc/apt/sources.list.d; \
    echo $(uname -m) > /tmp/arch; \
    if [ $(cat /tmp/arch) != 'x86_64' ] && grep -q -v "i.86" /tmp/arch; then \
        mv trusty-ports.list trusty.list; \
        mv xenial-ports.list xenial.list; \
    else \
        rm *-ports.list; \
    fi

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends --allow-downgrades \
    python-dev python-pip python-setuptools python-wheel \
    python3.5-dev python3-pip python3-setuptools python3-wheel \
    python3.4-dev findutils=4.4.2-7 python3.6-dev \
    libmysqlclient-dev mysql-client curl unzip build-essential \
    git postgresql-client tzdata libpq-dev

# User
RUN useradd --uid=$UID --create-home patchwork

# Timezone
RUN rm /etc/localtime; ln -s /usr/share/zoneinfo/$TZ /etc/localtime

# Python requirements.
# If you update requirements, you should rebuild the container.
# entrypoint.sh will prompt you to do this.
# we install both Python 2 and Python 3 versions so you can use either
COPY requirements-*.txt /tmp/
RUN pip3 install virtualenv tox && \
    pip3 install -r /tmp/requirements-dev.txt
RUN pip2 install virtualenv tox && \
    pip2 install -r /tmp/requirements-dev.txt
# we deliberately leave the requirements files in tmp so we can
# ping the user in entrypoint.sh if the change them!

COPY tools/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
USER patchwork
WORKDIR /home/patchwork/patchwork
