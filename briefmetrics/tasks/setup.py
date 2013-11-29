# TODO: Move into __init__.py ala model?
from celery import Celery, signals, schedules

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
            ADMINS = [('Briefmetrics Celery', 'shazow+briefmetrics+errors@gmail.com')]
            SERVER_EMAIL = 'service+celery@briefmetrics.com'

        CELERYBEAT_SCHEDULE = {
            'send-reports': {
                'task': 'briefmetrics.tasks.report.send_all',
                'schedule': schedules.crontab(minute=0), # Hourly
            },
            'dry-run': {
                'task': 'briefmetrics.tasks.report.dry_run',
                'schedule': schedules.crontab(minute=0, hour=14), # Daily
            },
        }

    celery.config_from_object(Config)


ini_file = os.environ.get('INI_FILE')
if ini_file:
    init(paste.deploy.appconfig('config:' + ini_file, relative_to='.'))


@signals.worker_init.connect
def bootstrap_pyramid(signal, sender):
    from pyramid.paster import bootstrap
    booted = bootstrap(ini_file)
    sender.app.request = booted['request']


@signals.task_postrun.connect
def close_session(*args, **kwargs):
    from briefmetrics.model.meta import Session
    Session.remove()
