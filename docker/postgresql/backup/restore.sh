#!/bin/bash
set -e

usage() {
    echo "$0 DATABASE RESTOREFILE"
}

database="$1"
if [ -z "$database" ]; then
    usage
    exit -1
fi;

restore_to="$2"
if [[ -z "$restore_to" ]]; then
    usage
    exit -1
fi

if [[ ! -f "$restore_to" ]]; then
    echo "Restore file does not exist: $restore_to"
    exit -2
fi

echo "Making a pre-restore backup..."
./backup.sh "$database" prerestore

echo "Stopping web app..."
docker stop briefmetrics-uwsgi
trap "docker start briefmetrics-uwsgi" EXIT

echo "Dropping the old database..."
docker exec -i db dropdb "$database" || echo "No database, skipping"

echo "Restoring from backup..."
docker exec -i db createdb "$database"
gunzip -c "$restore_to" | docker exec -i db psql "$database"

echo "Done."
