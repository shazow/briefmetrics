from celery import Celery
from celery.signals import worker_init

import os
import paste.deploy

celery = Celery(
    'briefmetrics',
    include=['briefmetrics.tasks']
)

def init(settings):
    class Config:
        BROKER_URL = settings['celery.broker']

    celery.config_from_object(Config)


ini_file = os.environ.get('INI_FILE')
if ini_file:
    init(paste.deploy.appconfig('config:' + ini_file, relative_to='.'))

@worker_init.connect
def bootstrap_pyramid(signal, sender):
    from pyramid.paster import bootstrap
    booted = bootstrap(ini_file)
    sender.app.request = booted['request']
    print signal, sender, sender.app
