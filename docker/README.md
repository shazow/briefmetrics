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
  --log-driver=syslog \
  shazow/postgresql
```


## uwsgi

```
docker run --name=briefmetrics -d \
  --log-driver=syslog \
  --volume=~/volumes/briefmetrics/src:/app/src \
  --link=postgresql:db \
  shazow/uwsgi-python
```


## nginx

```
docker run --name=nginx -d -p 80:80 -p 443:443 \
  --log-driver=syslog \
  --volume=~/volumes/nginx/sites:/etc/nginx/sites-enabled:ro \
  --volume=~/volumes/nginx/certs:/etc/nginx/certs:ro \
  --volume=~/volumes/nginx/www:/var/www:ro \
  --link=briefmetrics:briefmetrics \
  shazow/nginx
```
