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
    report = model.Session.query(model.Report).options(
        orm.joinedload(model.Report.account),
        orm.joinedload(model.Report.users),
    ).get(report_id)
    if not report:
        logger.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send_weekly(celery.request, report, pretend=pretend)


@periodic_task(ignore_result=True, run_every=crontab(hour=8))
def send_all(since_time=None, async=True, pretend=False, max_num=None):
    since_time = since_time or now()

    q = model.Session.query(model.Report).filter(
        (model.Report.time_next <= since_time) | (model.Report.time_next == None)
    )
    reports = q.all()

    send_fn = send_weekly
    if async:
        send_fn = send_weekly.delay

    for i, report in enumerate(reports):
        if max_num and i > max_num:
            logger.info('max_num reached, stopping send_all.')
            break

        send_fn(report_id=report.id, since_time=since_time, pretend=pretend)

    logger.info('Queued %d reports for sending.' % len(reports))
