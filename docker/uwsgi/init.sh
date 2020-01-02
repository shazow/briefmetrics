#!/bin/sh
set -x -o pipefail

if [[ ! -f "/home/app/env/bin/activate" ]]; then
    # NOTE: Must use the same python to make the venv as uwsgi has a plugin for. As of 2020-01-02, that's python3.7
    python3.7 -m venv --system-site-packages /home/app/env
    . /home/app/env/bin/activate
else
    . /home/app/env/bin/activate
fi

cd /home/app/src
pip install psycopg2-binary
python setup.py develop
make clean
make -e "INI_FILE=${INI_FILE}"
uwsgi --ini "${INI_FILE}"
