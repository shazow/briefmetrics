import random
import datetime

from sqlalchemy import orm
from unstdlib import now
from celery.utils.log import get_task_logger

from briefmetrics import model
from briefmetrics import api

from .setup import celery


log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def send(report_id, since_time=None, pretend=False):
    """Task to send a specific weekly report (gets created by send_all)."""
    report = model.Session.query(model.Report).options(
        orm.joinedload(model.Report.account),
        orm.joinedload(model.Report.users),
    ).get(report_id)
    if not report:
        log.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send(celery.request, report, pretend=pretend)


@celery.task(ignore_result=True)
def send_all(since_time=None, async=True, pretend=False, max_num=None):
    """Send all outstanding reports."""
    send_fn = send
    if async:
        send_fn = send.delay

    num_reports = 0
    reports = api.report.get_pending(since_time=since_time, max_num=max_num)

    for num_reports, report in enumerate(reports):
        send_fn(report_id=report.id, since_time=since_time, pretend=pretend)

    log.info('Queued %d reports for sending.' % num_reports)


@celery.task(ignore_result=True)
def dry_run(num_extra=5, async=True):
    all_reports = model.Session.query(model.Report).options(orm.joinedload_all('account.user')).all()

    # Start with all paying customers
    report_queue = [r for r in all_reports if r.account.user.payment]

    # Add some extra random customers
    while num_extra:
        if len(report_queue) > len(all_reports) * 0.7:
            # Give up
            break

        r = random.choice(all_reports)
        if r in report_queue:
            continue

        report_queue.append(r)
        num_extra -= 1

    since_time = now() - datetime.timedelta(days=14)

    send_fn = send
    if async:
        send_fn = send.delay

    log.info('Starting dry run for %d reports.' % len(report_queue))
    for report in report_queue:
        log.info('Dry run for report: %s' % report.display_name)
        send_fn(report_id=report.id, since_time=since_time, pretend=True)
