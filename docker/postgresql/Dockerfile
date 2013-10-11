# DOCKER-VERSION 0.6.1
# Borrowed from https://github.com/vvlad/dockerfiles-postgresql-9.3
#
# First run:
#     $ docker build -t postgresql -rm=true .
#     $ ID=$(docker run -e "CREATE_DB=foo" -v "path/to/socks:/var/run/postgresql" -d postgresql)
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
RUN apt-get -y install wget pgtune apg
RUN wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Suspend services autostart
RUN echo "#!/bin/sh\nexit 101" > /usr/sbin/policy-rc.d; chmod +x /usr/sbin/policy-rc.d

RUN apt-get -y update
RUN apt-get -y install postgresql-9.3
RUN pg_dropcluster 9.3 main

# Resume services autostart
RUN rm /usr/sbin/policy-rc.d

ADD init.sh /init.sh

EXPOSE  :5432
VOLUME  ["/var/lib/postgresql", "/etc/postgresql", "/app/socks"]
CMD     ["/init.sh"]
