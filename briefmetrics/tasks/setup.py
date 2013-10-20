# TODO: Move into __init__.py ala model?
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
        CELERY_POOL_RESTARTS = True
        CELERY_DISABLE_RATE_LIMITS = True
        CELERY_TIMEZONE = 'US/Eastern'

        if settings.get('mail.enabled', 'false') != 'false':
            CELERY_SEND_TASK_ERROR_EMAILS = True
            EMAIL_HOST = settings.get('mail.host')
            EMAIL_PORT = settings.get('mail.port')
            ADMINS = [('Briefmetrics Celery', 'errors@briefmetrics.com')]
            SERVER_EMAIL = 'service+celery@briefmetrics.com'

    celery.config_from_object(Config)


ini_file = os.environ.get('INI_FILE')
if ini_file:
    init(paste.deploy.appconfig('config:' + ini_file, relative_to='.'))


@worker_init.connect
def bootstrap_pyramid(signal, sender):
    from pyramid.paster import bootstrap
    booted = bootstrap(ini_file)
    sender.app.request = booted['request']
