import logging
import datetime
from itertools import groupby
from unstdlib import now
from sqlalchemy import orm

from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics import model

from . import google as api_google, email as api_email


log = logging.getLogger(__name__)


def _cumulative_by_month(rows, month_idx=1, value_idx=2):
    max_value = 0
    sum = 0

    months = []
    for month_num, data in groupby(rows, lambda r: r[month_idx]):
        rows = []
        for row in data:
            rows.append(sum)
            sum += float(row[value_idx])

        rows.append(sum)
        max_value = max(max_value, sum)
        sum = 0

        months.append(rows)

    return months, max_value


def fetch_weekly(request, report, date_start):
    date_end = date_start + datetime.timedelta(days=6)

    oauth = api_google.auth_session(request, report.account.oauth_token)
    q = api_google.Query(oauth)

    c = Context(report=report, date_start=date_start, date_end=date_end)
    c.base_url = report.remote_data.get('websiteUrl', '')
    c.date_next = date_start + datetime.timedelta(days=7)
    c.subject = "Weekly report for %s" % report.display_name

    params = {
        'id': report.remote_data['id'],
        'date_start': date_start,
        'date_end': date_end,
    }

    c.report_summary = q.report_summary(**params)
    c.report_referrers = q.report_referrers(**params)
    c.report_pages = q.report_pages(**params)
    c.report_social = q.report_social(**params)

    r = q.report_historic(**params)
    r, max_value = _cumulative_by_month(r.get('rows', []))

    c.historic_data = encode_rows(r, max_value)
    c.total_current = r[1][-1]
    c.total_last = r[0][-1]
    c.total_last_relative = r[0][len(r[1]) - 1]

    return c


def render_weekly(request, user, context):
    context.user = user

    return Controller(request, context=context)._render_template('report.mako')


def send_weekly(request, report, since_time=None):
    since_time = since_time or now()

    if report.time_next and report.time_next > since_time:
        log.warn('send_weekly too early, skipping for report: %s' % report.id)
        return

    # Last Sunday
    date_start = since_time.date() - datetime.timedelta(days=6) # Last week
    date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week

    context = fetch_weekly(request, report, date_start)

    log.info('Sending report to [%d] users: %s' % (len(report.users), report.display_name))

    for user in report.users:
        html = render_weekly(request, user, context)

        message = api_email.create_message(request,
            to_email=user.email,
            subject=context.subject, 
            html=html,
        )
        api_email.send_message(request, message)

    report.time_last = now()
    report.time_next = datetime.datetime(*date_start.timetuple()[:3]) + datetime.timedelta(days=7)

    model.Session.commit()


def send_all(request, since_time=None):
    since_time = since_time or now()

    q = model.Session.query(model.Report).filter(
        (model.Report.time_next <= since_time) | (model.Report.time_next == None)
    )
    q = q.options(orm.joinedload(model.Report.account))
    reports = q.all()

    for report in reports:
        send_weekly(request, report, since_time)