#!/bin/bash
set -e

echo "Checking for local postgres..."
if brew services list | grep "postgresql\s*started" > /dev/null; then
    echo "OK."
else
    echo "ERROR: local postgres not found!"
    echo
    echo "Please make sure postgres is installed and running locally:"
    echo "  $ brew install postgresql"
    echo "  $ brew services start postgresql"
    exit 1
fi

if ! echo "select 'yes' from pg_database where datname='siphon_web_local';" | psql -h localhost postgres | grep yes > /dev/null; then
    echo "Local database 'siphon_web_local' does not exist, creating it..."
    echo "create database siphon_web_local;" | psql -h localhost postgres
    echo "Done."
fi

export SIPHON_ENV=dev
./manage.py migrate && ./manage.py gruntserver 8080
