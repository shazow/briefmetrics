import logging
import datetime
from itertools import groupby
from unstdlib import now

from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib import changes
from briefmetrics import model

from . import google as api_google, email as api_email, account as api_account


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
    c.date_next = date_end + datetime.timedelta(days=9)

    c.subject = u"Weekly report \u2019til %s: %s" % (
        date_end.strftime('%b %d'),
        report.display_name,
    )
    c.report = report

    params = {
        'id': report.remote_data['id'],
        'date_start': date_start,
        'date_end': date_end,
    }

    c.has_data = True
    c.report_pages = q.report_pages(**params)
    if not c.report_pages.get('rows'):
        # No data :(
        c.subject = u"Problem with your Briefmetrics account"
        c.has_data = False
        return c

    c.report_summary = q.report_summary(**params)
    c.report_referrers = q.report_referrers(**params)
    c.report_social = q.report_social(**params)

    r = q.report_historic(**params)
    r, max_value = _cumulative_by_month(r.get('rows', []))

    c.historic_data = encode_rows(r, max_value)
    c.total_current = r[1][-1]
    c.total_last = r[0][-1]
    c.total_last_relative = r[0][len(r[1]) - 1]
    c.changes = changes
    c.owner = report.account.user

    return c


def render_weekly(request, user, context):
    context.user = user

    template = 'email/report.mako'
    if not context.has_data:
        template = 'email/error_empty.mako'

    return Controller(request, context=context)._render_template(template)


def send_weekly(request, report, since_time=None, pretend=False):
    since_time = since_time or now()

    if report.time_next and report.time_next > since_time:
        log.warn('send_weekly too early, skipping for report: %s' % report.id)
        return

    owner = report.account.user
    if owner.num_remaining is not None and owner.num_remaining <= 0:
        if not owner.stripe_customer_id:
            # TODO: Send final email?
            log.info('User [%d] expired, deleting report: %s' % (owner.id, report.display_name))
            report.delete()
            model.Session.commit()
            return

        # Create subscription for customer
        api_account.start_subscription(owner)
        owner.num_remaining = None

    # Last Sunday
    date_start = since_time.date() - datetime.timedelta(days=6) # Last week
    date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week

    context = fetch_weekly(request, report, date_start)

    send_users = report.users
    if not context.has_data:
        send_users = [report.account.user]

    log.info('Sending report to [%d] users: %s' % (len(send_users), report.display_name))

    for user in report.users:
        html = render_weekly(request, user, context)

        if pretend:
            continue

        message = api_email.create_message(request,
            to_email=user.email,
            subject=context.subject, 
            html=html,
        )
        api_email.send_message(request, message)

    if pretend:
        return

    if context.has_data and owner.num_remaining:
        owner.num_remaining -= 1

    report.time_last = now()
    if not report.time_next:
        report.time_next = datetime.datetime(*date_start.timetuple()[:3]) + datetime.timedelta(days=8)

    report.time_next += datetime.timedelta(days=7)

    # TODO: Preferred time

    model.Session.commit()
