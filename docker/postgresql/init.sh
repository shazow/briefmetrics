#!/bin/sh

PATH=/bin:/sbin:/usr/bin:/usr/sbin

IP_ADDRESS="$(ip addr show eth0 | grep 'inet ' | awk '{ print $2 }' | cut -d '/' -f1)"

POSTGRES_BIN="/usr/lib/postgresql/9.3/bin/postgres"
POSTGRES_CONFIG="/etc/postgresql/9.3/main/postgresql.conf"


if [ ! -d /var/lib/postgresql/9.3/main ] ; then
    cat > "/etc/postgresql/9.3/main/pg_hba.conf" << EOF
local   all             postgres                                trust
host    all             all         0.0.0.0/0                   md5
EOF
    pg_createcluster 9.3 main
    pg_ctlcluster 9.3 main start
    password=${MASTER_PASSWORD:-$(< /dev/urandom tr -dc A-Za-z0-9 | head -c 16)}
    psql -U postgres -c "ALTER USER postgres WITH PASSWORD '$password';" &> /dev/null
    psql -U postgres -c "CREATE DATABASE db;"

    pg_ctlcluster 9.3 main stop

    echo "* Credentials: url=\"postgres://postgres:$password@$IP_ADDRESS/db\""
    exit 0
fi

su postgres -c "$POSTGRES_BIN -c config_file=\"$POSTGRES_CONFIG\" -c listen_addresses='*'"
