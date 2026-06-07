FROM ghcr.io/getpatchwork/pyenv:latest

# Match the host user's UID so the container can write to bind-mounted volumes.
# Ubuntu 24.04 ships with an 'ubuntu' user (UID 1000); we just remap it.
ARG UID=1000
ARG GID=1000
RUN groupmod -g "${GID}" ubuntu && usermod -u "${UID}" ubuntu && chown -R ubuntu:ubuntu /home/ubuntu

ARG TZ="Australia/Canberra"
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PROJECT_HOME=/home/ubuntu/patchwork
ENV DJANGO_SETTINGS_MODULE=patchwork.settings.dev

RUN rm -f /etc/localtime; ln -s /usr/share/zoneinfo/$TZ /etc/localtime

RUN eval "$(pyenv init -)"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    default-mysql-client \
    libpq-dev \
    libsqlite3-dev \
    postgresql-client \
    sqlite3 \
    tzdata \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install wheel tox

# we deliberately leave the requirements files in /opt so we can ping the user
# in entrypoint.sh if they change
COPY requirements-dev.txt requirements-test.txt /opt/
RUN pip install -r /opt/requirements-dev.txt

COPY tools/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
USER ubuntu
WORKDIR /home/ubuntu/patchwork
