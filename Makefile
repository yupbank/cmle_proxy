VERSION=1.0
PROJECT_ID=kubeflow
PROJECT=gcr.io/${PROJECT_ID}

all: build

build:
	docker build --pull -t ${PROJECT}/http-proxy:${VERSION} .

push: build
	gcloud docker -- push ${PROJECT}/http-proxy:${VERSION}

.PHONY: all build push
