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
def send_weekly(report_id, since_time=None, pretend=False):
    """Task to send a specific weekly report (gets created by send_all)."""
    report = model.Session.query(model.Report).options(
        orm.joinedload(model.Report.account),
        orm.joinedload(model.Report.users),
    ).get(report_id)
    if not report:
        log.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send_weekly(celery.request, report, pretend=pretend)


@celery.task(ignore_result=True)
def send_all(since_time=None, async=True, pretend=False, max_num=None):
    """Send all outstanding reports."""
    since_time = since_time or now()

    q = model.Session.query(model.Report).filter(
        (model.Report.time_next <= since_time) | (model.Report.time_next == None)
    )
    reports = q.all()

    send_fn = send_weekly
    if async:
        send_fn = send_weekly.delay

    for i, report in enumerate(reports):
        if max_num and i >= max_num:
            log.info('max_num reached, stopping send_all.')
            break

        send_fn(report_id=report.id, since_time=since_time, pretend=pretend)

    log.info('Queued %d reports for sending.' % len(reports))


def dry_run(num_extra=5, async=True):
    all_reports = model.Session.query(model.Report).options(orm.joinedload_all('account.user')).all()

    # Start with all paying customers
    report_queue = [r for r in all_reports if r.account.user.stripe_customer_id]

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

    send_fn = send_weekly
    if async:
        send_fn = send_weekly.delay

    log.info('Starting dry run for %d reports.' % len(report_queue))
    for report in report_queue:
        log.info('Dry run for report: %s' % report.display_name)
        send_fn(report_id=report.id, since_time=since_time, pretend=True)
