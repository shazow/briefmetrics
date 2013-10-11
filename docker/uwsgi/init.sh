#!/bin/sh

pip install uwsgi PasteDeploy

virtualenv --system-site-packages /app/env
. /app/env/bin/activate

cd /app/src
python setup.py develop
make -e "INI_FILE=production.ini"
uwsgi --ini-paste production.ini
