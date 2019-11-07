#!/bin/sh
python -m venv --system-site-packages /home/app/env
. /home/app/env/bin/activate

cd /home/app/src
python setup.py develop
make -e "INI_FILE=${INI_FILE}"
uwsgi --ini "${INI_FILE}"
