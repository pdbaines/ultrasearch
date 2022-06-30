BASE=pdbaines83
PROJECT=ultrasearch
VERSION=0.0.1

build:
	docker build -t ${BASE}/${PROJECT}:${VERSION} .

debug:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION} /bin/sh

run:
	docker run --rm -it --env-file=.env ${BASE}/${PROJECT}:${VERSION}
