import time
import logging
import datetime
import random

from unstdlib import now

from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.report import WeeklyReport, EmptyReportError
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


def add_subscriber(report_id, email, display_name):
    u = model.User.get_or_create(email=email)
    if not u.id:
        u.display_name = display_name
        # FIXME: Start on a different plan? Or no plan == subscriber?
        u.num_remaining = 2

    model.Subscription.create(user=u, report_id=report_id)
    model.Session.commit()

    return u


# Reporting tasks:

def fetch_weekly(request, report, date_start, google_query=None):
    if not google_query:
        oauth = api_google.auth_session(request, report.account.oauth_token)
        google_query = api_google.create_query(request, oauth)

    owner = report.account.user
    if not owner.stripe_customer_id and owner.num_remaining is not None and owner.num_remaining <= 1:
        request.flash(h.literal('''
            <strong>This is your final report. :(</strong><br />
            Please <a href="https://briefmetrics.com/settings">add a credit card now</a> to keep receiving Briefmetrics reports.
        '''))

    r = WeeklyReport(report, date_start)

    try:
        r.fetch(google_query)
    except EmptyReportError:
        r.tables = {}
        return r

    return r


def render(request, template, context=None):
    return Controller(request, context=context)._render_template(template)


def send_weekly(request, report, since_time=None, pretend=False):
    t = time.time()

    since_time = since_time or now()

    if not pretend and report.time_next and report.time_next > since_time:
        log.warn('send_weekly too early, skipping for report: %s' % report.id)
        return

    owner = report.account.user
    if not pretend and owner.num_remaining is not None and owner.num_remaining <= 0:
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
    subject = report_context.get_subject()
    template = 'email/report.mako'
    if not report_context.data:
        send_users = [report.account.user]
        template = 'email/error_empty.mako'

    log.info('Sending report to [%d] users: %s' % (len(send_users), report.display_name))

    debug_sample = request.registry.settings.get('email.debug_sample', 1)
    debug_bcc = owner.plan.id != 'trial' or not report.time_next or random.random() < debug_sample

    for user in report.users:
        html = render(request, template, Context({
            'user': user,
            'report': report_context,
        }))

        message = api_email.create_message(request,
            to_email=user.email,
            subject=subject, 
            html=html,
            debug_bcc=debug_bcc,
        )

        if pretend:
            continue

        api_email.send_message(request, message)

    model.ReportLog.create_from_report(report,
        body=html,
        subject=subject,
        seconds_elapsed=time.time()-t,
        time_sent=None if pretend else now(),
    )

    if pretend:
        model.Session.commit()
        return

    if report_context.data and owner.num_remaining:
        owner.num_remaining -= 1

    report.time_last = now()
    report.time_next = report.next_preferred(since_time)

    model.Session.commit()
