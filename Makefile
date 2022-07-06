BASE=pdbaines83
PROJECT=ultrasearch
VERSION=0.0.1

build:
	docker build -t ${BASE}/${PROJECT}:${VERSION} .

debug:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION} /bin/sh

run:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION}

test:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION} pytest

tag:
	docker tag ${BASE}/${PROJECT}:${VERSION} ${PROJECT}

compose-run:
	docker compose exec console python run_celery.py

up:
	docker compose up

down:
	docker compose down -v

port-forward:
	k port-forward service/flower-ui 5555:5555
