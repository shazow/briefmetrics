#!/bin/sh
set -x -o pipefail

if [[ ! -f "/home/app/env/bin/activate" ]]; then
    python -m venv --system-site-packages /home/app/env
    . /home/app/env/bin/activate
    pip install psycopg2 PasteDeploy
else
    . /home/app/env/bin/activate
fi

cd /home/app/src
python setup.py develop
make -e "INI_FILE=${INI_FILE}"
uwsgi --ini "${INI_FILE}"
