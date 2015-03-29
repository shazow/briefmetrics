#!/bin/bash
# Backup all the things, and delete old backups.

# How many old backups should we keep?
NUM_OLD_BACKUPS=5


##

backup_cmd="$(dirname $0)/backup.sh"

function handle_database() {
    # Make a new backup
    $backup_cmd "$1"

    # Delete stale backups?
    num_backups="$(ls $database* 2> /dev/null | wc -l)"
    if [ "$num_backups" -le "$NUM_OLD_BACKUPS" ]; then
        return 0
    fi

    num_to_delete="$((num_backups-NUM_OLD_BACKUPS))"
    ls -t -- $databases* | tail -n $num_to_delete | xargs rm
}


handle_database "db"
