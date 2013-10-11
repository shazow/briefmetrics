#!/bin/sh

PATH=/bin:/sbin:/usr/bin:/usr/sbin

if [ ! -d /var/lib/postgresql/9.3/main ] ; then
	pg_dropcluster 9.3 main --stop 2> /dev/null
	pg_createcluster 9.3 main
	cat > "/etc/postgresql/9.3/main/pg_hba.conf" << EOF
local   all             postgres                                trust
host    all             all         0.0.0.0/0                   md5
EOF
	pg_ctlcluster 9.3 main start
	password=${MASTER_PASSWORD:-$(< /dev/urandom tr -dc A-Za-z0-9 | head -c 32)}
	psql -U postgres -c "ALTER USER postgres with password '$password';" >/dev/null 2>&1
	echo "  pass   $password"
	echo "  user   postgres"
	pg_ctlcluster 9.3 main stop
	exit 0
fi

if [ "$CREATE_DB" ]; then
    su postgres -c "createdb -O postgres \"$CREATE_DB\""
fi

pgtune -i /etc/postgresql/9.3/main/postgresql.conf -o /etc/postgresql/9.3/main/postgresql.conf  -TWeb -M`free  -ob| grep Mem: | awk '{ printf "%d",$2 }'`
su postgres -c "/usr/lib/postgresql/9.3/bin/postgres -c config_file='/etc/postgresql/9.3/main/postgresql.conf' -c unix_socket_directories='/app/socks'"
