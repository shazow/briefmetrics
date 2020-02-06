# First run:
#     $ docker build -t uwsgi -rm=true .
#     $ ID=$(docker run -v "path/to/src:/app/src" -v "path/to/socks:/app/socks" -d uwsgi)
#     $ docker wait $ID
#     $ docker logs $ID

FROM       python:alpine
MAINTAINER Andrey Petrov "andrey.petrov@shazow.net"

RUN apk add --update wget make libxslt-dev libxml2-dev g++ libjpeg-turbo-dev libpng-dev python3-dev postgresql-dev freetype-dev uwsgi-python3

RUN addgroup app && adduser -D -u 1000 -G app app
USER app:app
WORKDIR /home/app
RUN mkdir src env socks

ADD init.sh /init.sh

VOLUME  ["/home/app/src", "/home/app/env", "/home/app/socks"]
CMD     ["/init.sh"]
