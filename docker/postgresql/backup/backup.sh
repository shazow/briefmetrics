#!/bin/bash
database="$1"
if [ -z "$database" ]; then
    echo "Which database do you want to back up?"
    exit -1
fi;
prefix="$2"

title="${prefix}${database}_$(date -I)"

num="$(ls $title*.sql.gz 2> /dev/null | wc -l)"

backup_file="${title}.sql.gz"
if [ "$num" != "0" ]; then
    backup_file="${title}.${num}.sql.gz"
fi

# PostgreSQL:
pg_dump -U postgres -h 172.17.0.2 "$database" | gzip > "$backup_file"
