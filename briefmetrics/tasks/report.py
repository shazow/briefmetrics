from sqlalchemy import orm
from unstdlib import now
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from celery.task import periodic_task

from briefmetrics import model
from briefmetrics import api

from .setup import celery


logger = get_task_logger(__name__)


@celery.task(ignore_result=True)
def send_weekly(report_id, since_time=None):
    report = model.Report.get(report_id)
    if not report:
        logger.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send_weekly(celery.request, report)


@periodic_task(run_every=crontab(hour=10, minute=42, day_of_week='sun')) # FIXME: 'mon'
def send_all(report_id, since_time=None):
    since_time = since_time or now()

    q = model.Session.query(model.Report).filter(
        (model.Report.time_next <= since_time) | (model.Report.time_next == None)
    )
    q = q.options(orm.joinedload(model.Report.account))
    reports = q.all()

    for report in reports:
        send_weekly.delay(report_id=report.id, since_time=since_time)

    logger.info('Queued %d reports for sending.' % len(reports))
