import time
import logging
import datetime
import random

from unstdlib import now
from itertools import groupby

from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.report import WeeklyReport
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib import helpers as h
from briefmetrics import model

from . import google as api_google, email as api_email, account as api_account


log = logging.getLogger(__name__)


def create(account_id, remote_data=None, remote_id=None, display_name=None, subscribe_user_id=None, type=None):
    remote_id = remote_id or str(remote_data['id'])
    type = type or 'week'

    report = model.Report.get_or_create(account_id=account_id, remote_id=remote_id, type=type)
    if report.id:
        raise APIError("Report already exists.")

    if remote_data:
        report.remote_data = remote_data
        report.remote_id = str(remote_data['id'])
        report.display_name = h.human_url(remote_data['websiteUrl']) or remote_data['name']

    if remote_id:
        report.remote_id = str(remote_id)

    if display_name:
        report.display_name = display_name

    if subscribe_user_id:
        model.Subscription.create(user_id=subscribe_user_id, report=report)

    model.Session.commit()
    return report


# Reporting tasks:

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
    oauth = api_google.auth_session(request, report.account.oauth_token)
    q = api_google.Query(oauth)

    r = WeeklyReport(report, date_start)

    params = r.get_query_params()

    # Short circuit for no data
    data = q.report_pages(**params)
    if not data.get('rows'):
        return r

    r.data.pages = data['rows']
    r.data.summary = q.report_summary(**params).get('rows')
    r.data.referrers = q.report_referrers(**params).get('rows')
    r.data.social = q.report_social(**params).get('rows')

    # Historic chart and intro
    data = q.report_historic(**params)['rows']
    monthly_data, max_value = _cumulative_by_month(data)
    last_month, current_month = monthly_data

    r.data.historic_data = encode_rows(monthly_data, max_value)
    r.data.total_current = current_month[-1]
    r.data.total_last = last_month[-1]
    r.data.total_last_relative = last_month[len(current_month)-1]

    return r


def render(request, template, context=None):
    return Controller(request, context=context)._render_template(template)


def send_weekly(request, report, since_time=None, pretend=False):
    t = time.time()

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

            subject = u"Your Briefmetrics trial is over"
            html = render(request, 'email/error_trial_end.mako')
            message = api_email.create_message(request,
                to_email=owner.email,
                subject=subject,
                html=html,
            )
            api_email.send_message(request, message)

            return

        # Create subscription for customer
        api_account.start_subscription(owner)
        owner.num_remaining = None

    # Last Sunday
    date_start = since_time.date() - datetime.timedelta(days=6) # Last week
    date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week

    report_context = fetch_weekly(request, report, date_start)

    send_users = report.users
    subject= report_context.get_subject()
    template = 'email/report.mako'
    if not report_context.data:
        send_users = [report.account.user]
        template = 'email/error_empty.mako'

    log.info('Sending report to [%d] users: %s' % (len(send_users), report.display_name))

    debug_sample = request.registry.settings.get('email.debug_sample', 1)
    debug_bcc = owner.plan.id != 'trial' or random.random() < debug_sample

    for user in report.users:
        html = render(request, template, Context({
            'user': user,
            'report': report_context,
        }))

        if pretend:
            continue

        message = api_email.create_message(request,
            to_email=user.email,
            subject=subject, 
            html=html,
            debug_bcc=debug_bcc,
        )
        api_email.send_message(request, message)

    if pretend:
        return

    if report_context.data and owner.num_remaining:
        owner.num_remaining -= 1

    report.time_last = now()
    if not report.time_next:
        report.time_next = datetime.datetime(*date_start.timetuple()[:3]) + datetime.timedelta(days=8)

    # TODO: Preferred time
    # XXX: Is this done?
    report.time_next += datetime.timedelta(days=7)

    model.ReportLog.create_from_report(report,
        body=html,
        subject=subject,
        seconds_elapsed=time.time()-t,
    )

    model.Session.commit()
