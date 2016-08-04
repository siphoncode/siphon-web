#!/bin/bash
echo "Setting up env variables..."
eval "$(docker-machine env default)"

if [ "$1" = "--psql" ]; then
    docker run -it --link postgres_web --rm --env='PGPASSWORD=web' postgres:9.4.5 sh -c 'exec psql -h "$POSTGRES_WEB_PORT_5432_TCP_ADDR" -p "$POSTGRES_WEB_PORT_5432_TCP_PORT" -U web'
    exit 0
fi

if [ "$1" = "--logs" ]; then
    docker exec web tail -F /volumes/logs/nginx-error.log /volumes/logs/nginx-access.log /volumes/logs/django.log /volumes/logs/uwsgi.log
    exit 0
fi

# Inserts $SIPHON_ENV and other placeholders
COMPOSE_FILE="compose.yml"
TMP_COMPOSE_FILE=".tmp-compose.yml"
rm -f $TMP_COMPOSE_FILE
cat $COMPOSE_FILE \
    | sed -e 's/$SIPHON_ENV/staging/g' \
    | sed -e 's/$CLI_HOST/local.getsiphon.com/g' \
    | sed -e 's/$CLI_PORT/80/g' > "${TMP_COMPOSE_FILE}"

# echo "Stopping any running containers..."
#docker-compose -f compose.yml stop
#docker stop $(docker ps -a -q)

echo "Building and running web containers..."
docker-compose -f $TMP_COMPOSE_FILE build && docker-compose -f $TMP_COMPOSE_FILE up && rm -f $TMP_COMPOSE_FILE
