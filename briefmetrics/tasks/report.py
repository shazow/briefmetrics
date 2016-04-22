import random
import datetime

from sqlalchemy import orm
from unstdlib import now, timestamp_from_datetime, datetime_from_timestamp
from celery.utils.log import get_task_logger

from briefmetrics import model
from briefmetrics import api

from .setup import celery


log = get_task_logger(__name__)


def _to_datetime(t):
    if not t:
        return t
    if isinstance(t, float):
        return datetime_from_timestamp(t)
    return t

def _from_datetime(t):
    if not t:
        return t
    return timestamp_from_datetime(t)


@celery.task(ignore_result=True)
def send(report_id, since_time=None, pretend=False):
    """Task to send a specific weekly report (gets created by send_all)."""
    since_time = _to_datetime(since_time)

    session = model.Session()
    report = session.query(model.Report).options(
        orm.joinedload(model.Report.account),
        orm.joinedload(model.Report.users),
    ).get(report_id)
    if not report:
        log.warn('Invalid report id, skipping: %s' % report_id)
        return

    api.report.send(celery.request, report, since_time=since_time, pretend=pretend, session=session)


@celery.task(ignore_result=True)
def send_all(since_time=None, async=True, pretend=False, max_num=None):
    """Send all outstanding reports."""
    since_time = _to_datetime(since_time)

    send_fn = send
    if async:
        send_fn = send.delay

    num_reports = 0
    reports = api.report.get_pending(since_time=since_time, max_num=max_num)

    for num_reports, report in enumerate(reports):
        send_fn(report_id=report.id, since_time=_from_datetime(since_time), pretend=pretend)

    log.info('Queued %d reports for sending.' % num_reports)


@celery.task(ignore_result=True)
def dry_run(num_extra=5, filter_account=None, async=True):
    q = model.Session.query(model.Report).options(orm.joinedload_all('account.user'))
    if filter_account:
        q = q.filter(model.Report.account_id==filter_account)

    all_reports = q.all()

    report_queue = all_reports
    # Start with all paying customers
    if not filter_account:
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
        send_fn(report_id=report.id, since_time=_from_datetime(since_time), pretend=True)
