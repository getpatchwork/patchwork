MANAGE_PY := docker-compose run --rm web python manage.py

default:
	@echo "Call a specific subcommand"
	@exit 1

.state/docker-build: docker-compose.yml tools/docker/Dockerfile requirements-dev.txt
	docker-compose build
	mkdir -p .state
	touch .state/docker-build

build:
	docker-compose build
	mkdir -p .state
	touch .state/docker-build

serve: .state/docker-build
	docker-compose up

tests: .state/docker-build
	docker-compose run -e TOXENV=${TOXENV} --rm web tox

manage: .state/docker-build
	$(MANAGE_PY) $(CMD)

dbshell: .state/docker-build
	$(MANAGE_PY) dbshell

shell: .state/docker-build
	$(MANAGE_PY) shell

migrate: .state/docker-build
	$(MANAGE_PY) migrate

makemigrations: .state/docker-build
	$(MANAGE_PY) makemigrations

dbbackup: .state/docker-build
	$(MANAGE_PY) dbbackup

dbrestore: .state/docker-build
	$(MANAGE_PY) dbrestore

.PHONY: default build serve tests dbshell shell manage migrate makemigrations dbbackup dbrestore
