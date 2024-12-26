FROM ghcr.io/getpatchwork/pyenv:latest

ARG UID=1000
ARG GID=1000

ARG TZ="Australia/Canberra"
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV PROJECT_HOME /home/patchwork/patchwork
ENV DJANGO_SETTINGS_MODULE patchwork.settings.dev

RUN groupadd -o --gid=$GID patchwork && \
    useradd --uid=$UID --gid=$GID --create-home patchwork
RUN rm -f /etc/localtime; ln -s /usr/share/zoneinfo/$TZ /etc/localtime

RUN eval "$(pyenv init -)"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmysqlclient-dev \
    libpq-dev \
    libsqlite3-dev \
    mysql-client \
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
USER patchwork
WORKDIR /home/patchwork/patchwork
