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
def send_weekly(report_id, since_time=None, pretend=False):
    report = model.Report.get(report_id)
    if not report:
        logger.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send_weekly(celery.request, report, pretend=pretend)


@periodic_task(ignore_result=True, run_every=crontab(hour=8))
def send_all(since_time=None, async=True, pretend=False):
    since_time = since_time or now()

    q = model.Session.query(model.Report).filter(
        (model.Report.time_next <= since_time) | (model.Report.time_next == None)
    )
    q = q.options(orm.joinedload(model.Report.account))
    reports = q.all()

    send_fn = send_weekly
    if async:
        send_fn = send_weekly.delay

    for report in reports:
        send_fn(report_id=report.id, since_time=since_time, pretend=pretend)

    logger.info('Queued %d reports for sending.' % len(reports))
