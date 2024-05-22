#!/bin/sh
DOCKER_BUILDKIT=1 docker build \
    --pull=false \
    -f .pipeline/blubber.yaml \
    --target testing \
    --platform linux/arm64 \
    -t bitu/testing .