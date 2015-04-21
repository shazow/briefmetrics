# Configs

*/etc/logrotate.d/docker*

```
/var/log/docker/*.log
{
	rotate 6
	monthly
	missingok
	notifempty
	delaycompress
	compress
	postrotate
		reload rsyslog >/dev/null 2>&1 || true
	endscript
}
```

*/etc/rsyslog.d/docker.conf*

```
# Split out 0123456789abc out of docker/0123456789abc[123456]
$template DockerPath,"/var/log/docker/%syslogtag:7:19%.log"
:syslogtag,startswith,"docker/" ?DockerPath
```

Run:

```
$ service rsyslog restart
```

# Dockers

## db

```
docker run --name=db -d \
  --restart=always \
  --log-driver=syslog \
  shazow/postgresql
```


## uwsgi

```
docker run --name=briefmetrics -d \
  --restart=always \
  --log-driver=syslog \
  --volume=$HOME/volumes/briefmetrics/src:/home/app/src \
  --link=db:db \
  --env=INI_FILE=staging.ini \
  shazow/python-uwsgi
```


```
docker run --rm -it \
  --volumes-from=briefmetrics \
  --link=db:db \
  --env=INI_FILE=staging.ini \
  shazow/python-uwsgi bash

```

## nginx

```
docker run --name=nginx -d -p 80:80 -p 443:443 \
  --restart=always \
  --log-driver=syslog \
  --volume=$HOME/volumes/nginx/sites:/etc/nginx/sites-enabled:ro \
  --volume=$HOME/volumes/nginx/certs:/etc/nginx/certs:ro \
  --volume=$HOME/volumes/nginx/www:/var/www:ro \
  --link=briefmetrics:briefmetrics \
  shazow/nginx
```
