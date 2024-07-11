#!/bin/bash
bitu migrate --no-input
bitu collectstatic

cd /usr/lib/python3/dist-packages/bitu/
export PYTHONPATH=/etc/bitu:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=settings

if [ ${UWSGI_HTTP_MODE} ]; then UWSGI_MODE="--http"; else UWSGI_MODE="--socket"; fi

uwsgi --plugins http,python3 "$UWSGI_MODE" ":${UWSGI_PORT:-8080}" --check-static /tmp/bitu/ --master --module bitu.wsgi:application --processes "${UWSGI_PROCESS_COUNT:-4}"
