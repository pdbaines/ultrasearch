BASE=pdbaines83
PROJECT=ultracal
VERSION=0.0.1

build:
        docker build -t ${BASE}/${PROJECT}:${VERSION} .