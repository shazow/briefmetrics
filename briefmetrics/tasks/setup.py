from celery import Celery
from celery.signals import worker_init

import os
import paste.deploy

settings = paste.deploy.appconfig('config:' + os.environ['INI_FILE'], relative_to='.')

@worker_init.connect
def bootstrap_pyramid(signal, sender):
    sender.app.settings = settings

celery = Celery(
    'briefmetrics',
    broker=settings.get('celery.broker'),
    backend=settings.get('celery.backend'),
)
