FROM ubuntu:18.04

ARG UID

# make sure the user has configured the '.env' file and quick fail if not

RUN echo $UID
RUN [ -n "$UID" ] || { echo "You must define UID in .env" 1>&2; exit 1; }

ARG TZ="Australia/Canberra"
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"
ENV PATH="/opt/pyenv/shims:/opt/pyenv/bin:$PATH"
ENV PYENV_ROOT="/opt/pyenv"
ENV PYENV_SHELL="bash"
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV PROJECT_HOME /home/patchwork/patchwork
ENV DJANGO_SETTINGS_MODULE patchwork.settings.dev

RUN useradd --uid=$UID --create-home patchwork
RUN rm /etc/localtime; ln -s /usr/share/zoneinfo/$TZ /etc/localtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    libbz2-dev \
    libffi-dev \
    libmysqlclient-dev \
    libpq-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl1.0-dev \
    mysql-client \
    postgresql-client \
    tzdata \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash && \
    git clone https://github.com/momo-lab/xxenv-latest $PYENV_ROOT/plugins/xxenv-latest && \
    pyenv update

RUN pyenv latest install 2.7 && \
    pyenv latest install 3.5 && \
    pyenv latest install 3.6 && \
    pyenv latest install 3.7

RUN pyenv global $(pyenv versions --bare | tac)

COPY requirements-*.txt /tmp/
RUN pip install tox tox-pyenv && \
    pip install -r /tmp/requirements-dev.txt

# we deliberately leave the requirements files in tmp so we can
# ping the user in entrypoint.sh if the change them!

COPY tools/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
USER patchwork
WORKDIR /home/patchwork/patchwork
