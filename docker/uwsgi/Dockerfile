# First run:
#     $ docker build -t uwsgi -rm=true .
#     $ ID=$(docker run -v "path/to/src:/app/src" -v "path/to/socks:/app/socks" -d uwsgi)
#     $ docker wait $ID
#     $ docker logs $ID

FROM       python:alpine
MAINTAINER Andrey Petrov "andrey.petrov@shazow.net"

RUN apk add --update wget make libxslt-dev libxml2-dev g++ libjpeg-turbo-dev libpng-dev python3-dev py-psycopg2 freetype-dev uwsgi-python3

ADD init.sh /init.sh

VOLUME  ["/app/src", "/app/env", "/app/socks"]
CMD     ["/init.sh"]
