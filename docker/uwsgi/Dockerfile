# DOCKER-VERSION 0.6.1
# Borrowed from https://github.com/vvlad/dockerfiles-postgresql-9.3
#
# First run:
#     $ docker build -t uwsgi -rm=true .
#     $ ID=$(docker run -v "path/to/src:/app/src" -v "path/to/socks:/app/socks" -d uwsgi)
#     $ docker wait $ID
#     $ docker logs $ID

FROM       ubuntu:12.04
MAINTAINER Andrey Petrov "andrey.petrov@shazow.net"


ENV DEBIAN_FRONTEND noninteractive

RUN locale-gen en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN echo 'deb http://us.archive.ubuntu.com/ubuntu/ precise universe' >> /etc/apt/sources.list
RUN apt-get -y update

# Install required packages
RUN apt-get -y install wget python-dev python-setuptools python-psycopg2 make
RUN easy_install pip
RUN pip install virtualenv

ADD init.sh /init.sh

EXPOSE  :8080
VOLUME  ["/app/src", "/app/env", "/app/socks"]
CMD     ["/init.sh"]
