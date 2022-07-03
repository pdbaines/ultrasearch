BASE=pdbaines83
PROJECT=ultrasearch
VERSION=0.0.1

build:
	docker build -t ${BASE}/${PROJECT}:${VERSION} .

debug:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION} /bin/sh

run:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION}

tag:
	docker tag ${BASE}/${PROJECT}:${VERSION} ${PROJECT}

compose-run:
	docker-compose exec console python run_celery.py
