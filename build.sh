#!/bin/sh
MACHINE_NAME=$(uname -m)

DOCKER_BUILDKIT=1 docker build \
    --pull=false \
    -f .pipeline/blubber.yaml \
    --target test \
    --platform "linux/$MACHINE_NAME" \
    --load \
    --tag localhost/bitu-testing \
    .
